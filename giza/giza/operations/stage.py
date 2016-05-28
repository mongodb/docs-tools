# Copyright 2015 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Amazon S3 staging system."""

import binascii
import collections
import functools
import hashlib
import logging
import os
import os.path
import pwd
import re
import stat
import sys
import threading

import argh
import boto.s3.connection
import boto.s3.bucket
import boto.s3.key
import boto.s3.lifecycle

from libgiza.git import GitRepo
from giza.config.helper import fetch_config

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

LOGGER = logging.getLogger('giza.operations.stage')
REDIRECT_PAT = re.compile('^Redirect 30[1|2|3] (\S+)\s+(\S+)', re.M)
FileUpdate = collections.namedtuple('FileUpdate', ['path', 'file_hash'])
AuthenticationInfo = collections.namedtuple('AuthenticationInfo', ['access_key', 'secret_key', 'username'])

CONFIG_PATH = '~/.config/giza-aws-authentication.conf'
SAMPLE_CONFIG = '''[authentication]
accesskey=<AWS access key>
secretkey=<AWS secret key>
'''


class Path(object):
    """Wraps Unix-style paths to ensure a normalized format."""
    def __init__(self, init):
        self.segments = init.split('/')

    def replace_prefix(self, orig, new):
        """Replace the "orig" string in this path ONLY if it is at the start."""
        cur = str(self)
        if cur.startswith(orig):
            return Path(str(self).replace(orig, new, 1))

        return Path(str(self))

    def ensure_prefix(self, prefix):
        """Prepend a string to this path ONLY if it does not already exist."""
        cur = str(self)
        if cur.startswith(prefix):
            return Path(str(self))

        return Path('/'.join((prefix, cur)))

    def __str__(self):
        """Format this path as a Unix-style path string."""
        return '/'.join(self.segments)


class BulletProofS3(object):
    """An S3 API that wraps boto to work around Amazon's 100-request limit."""
    THRESHOLD = 20

    def __init__(self, access_key, secret_key, bucket_name):
        self.access_key = access_key
        self.secret_key = secret_key
        self.name = bucket_name

        # For "dry" runs; only pretend to do anything.
        self.dry_run = False

        self.times_used = 0
        self._conn = None

    def get_connection(self):
        """Return a connection to S3. Not idempotent: will create a new connection
           after some number of calls."""
        if not self._conn or self.times_used > self.THRESHOLD:
            conn = boto.s3.connection.S3Connection(self.access_key, self.secret_key)
            self._conn = conn.get_bucket(self.name)
            self.times_used = 0

        self.times_used += 1
        return self._conn

    def list(self, prefix=None):
        """Returns a list of keys in this S3 bucket."""
        return self.get_connection().list(prefix=prefix)

    def get_redirect(self, name):
        """Return the destination redirect associated with a given source path."""
        k = boto.s3.key.Key(self.get_connection(), name)
        return k.get_redirect()

    def set_redirect(self, key, dest):
        """Redirect a given key to a destination."""
        if not self.dry_run:
            key.set_redirect(dest)

    def delete_keys(self, keys):
        """Delete the given list of keys."""
        if self.dry_run:
            keys = []

        return self.get_connection().delete_keys(keys)

    def copy(self, src_path, dest_name, **options):
        """Copy a given key to the given path."""
        if self.dry_run:
            return

        key = boto.s3.key.Key(self.get_connection())
        key.key = src_path
        key.copy(self.name, dest_name, **options)

    def upload_path(self, src, dest, **options):
        key = boto.s3.key.Key(self.get_connection())
        key.key = dest

        if self.dry_run:
            return key

        key.set_contents_from_filename(src, **options)
        return key


class StagingException(Exception):
    """Base class for all giza stage exceptions."""
    pass


class NoSuchEdition(StagingException):
    """An exception indicating that the requested edition does not exist."""
    pass


class SyncFileException(StagingException):
    """An exception indicating an S3 deletion error."""
    def __init__(self, path, reason):
        StagingException.__init__(self, 'Error syncing path: {0}'.format(path))
        self.reason = reason
        self.path = path


class SyncException(StagingException):
    """An exception indicating an error uploading files."""
    def __init__(self, errors):
        StagingException.__init__(self, 'Errors syncing data')
        self.errors = errors


class PoolWorker(threading.Thread):
    """A threaded worker that works on a queue of functions."""
    def __init__(self, **kwargs):
        threading.Thread.__init__(self, **kwargs)

        # Avoid needing to mutex-protect this queue by only ever appending to it
        self.tasks = []
        self.results = []
        self.i = 0

        self.semaphore = threading.Semaphore(0)

    def run(self):
        while True:
            self.semaphore.acquire()

            next_task = self.tasks[self.i]
            if next_task is None:
                return

            try:
                result = next_task()
                if result is not None:
                    self.results.append((next_task, result))
            except Exception as err:
                self.results.append((next_task, err))

            self.i += 1

    def add_task(self, task):
        """Adds a function to this work queue. The worker will exit if it
           reaches a None value."""
        self.tasks.append(task)
        self.semaphore.release()


def run_pool(tasks, n_workers=10, retries=1):
    """Run a list of tasks using a pool of threads. Return non-None results or
       exceptions as a list of (task, result) pairs in an arbitrary order."""
    assert retries >= 0

    results = []
    while retries >= 0:
        workers = []
        for _ in range(n_workers):
            worker = PoolWorker()
            worker.start()
            workers.append(worker)

        # Schedule tasks round-robin
        for i in range(len(tasks)):
            workers[i % n_workers].add_task(tasks[i])

        for worker in workers:
            worker.add_task(None)

        for worker in workers:
            worker.join()

        results = []
        for worker in workers:
            results.extend(worker.results)

        if not results:
            return []

        tasks = [result[0] for result in results]
        retries -= 1

    raise SyncException([result[1] for result in results])


def translate_htaccess(path):
    """Read a .htaccess file, and transform redirects into a mapping of redirects."""
    with open(path, 'r') as f:
        data = f.read()
        return dict([(x.lstrip('/'), y) for x,y in REDIRECT_PAT.findall(data)])

    return {}

class StagingCollector(object):
    """A dummy file collector interface that always reports files as having
       changed. Yields files and all symlinks.

       Obtain use_branch from StagingTargetConfig. If it is True,
       StagingCollector will only recurse into the directory given by branch."""
    def __init__(self, branch, use_branch, namespace):
        self.removed_files = []
        self.branch = branch
        self.use_branch = use_branch
        self.namespace = namespace

    def get_upload_set(self, root):
        return set(os.listdir(root))

    def collect(self, root, remote_keys):
        self.removed_files = []
        remote_hashes = {}
        whitelist = self.get_upload_set(root)

        LOGGER.info('Publishing %s', ', '.join(whitelist))

        # List all current redirects
        tasks = []
        for key in remote_keys:
            local_key = key.key.replace(self.namespace, '', 1)
            local_key = local_key.lstrip('/')

            # Don't register redirects for deletion in this stage
            if key.size == 0:
                continue

            # Check if we want to skip this path
            if local_key.split('/', 1)[0] not in whitelist:
                continue

            # Store its MD5 hash. Might be useless if encryption or multi-part
            # uploads are used.
            remote_hashes[local_key] = key.etag.strip('"')

            if not os.path.exists(os.path.join(root, local_key)):
                LOGGER.warn('Removing %s', os.path.join(root, local_key))
                self.removed_files.append(key.key)

        LOGGER.info('Running collection tasks')
        run_pool(tasks)
        LOGGER.info('Done. Scanning local filesystem')

        for basedir, dirs, files in os.walk(root, followlinks=True):
            # Skip branches we wish not to publish
            if basedir == root:
                dirs[:] = [d for d in dirs if d in whitelist]

            for filename in files:
                # Skip dotfiles
                if filename.startswith('.'):
                    continue

                path = os.path.join(basedir, filename)

                try:
                    local_hash = self.hash(path)
                except IOError:
                    continue

                remote_path = path.replace(root, '')
                if remote_hashes.get(remote_path, None) == local_hash:
                    continue

                yield FileUpdate(path, local_hash)

    def commit(self):
        pass

    def purge_now(self):
        pass

    @staticmethod
    def hash(path):
        """Return the cryptographic hash of the given file path as a byte
           sequence."""
        hasher = hashlib.md5()

        with open(path, 'rb') as input_file:
            while True:
                data = input_file.read(2**13)
                if not data:
                    break

                hasher.update(data)

        return hasher.hexdigest()


class DeployCollector(StagingCollector):
    def get_upload_set(self, root):
        if not self.use_branch:
            return set(os.listdir(root))

        # Special-case the root directory, because we want to publish only:
        # - Files
        # - The current branch (if published)
        # - Symlinks pointing to the current branch
        upload = set()
        for entry in os.listdir(root):
            path = os.path.join(root, entry)
            if os.path.isdir(path) and entry == self.branch:
                # This is the branch we want to upload
                upload.add(entry)
                continue

            # Only collect links that point to the current branch
            try:
                candidate = os.path.basename(os.path.realpath(path))
                if candidate == self.branch:
                    upload.add(entry)
                    continue
            except OSError:
                pass

        return upload


class Staging(object):
    # These files are always unique, and so there is no benefit in sharing them
    SHARED_CACHE_BLACKLIST = {'genindex.html', 'objects.inv', 'searchindex.js'}

    S3_OPTIONS = {'reduced_redundancy': True}
    RESERVED_BRANCHES = {'cache'}
    PAGE_SUFFIX = ''
    USE_CACHE = True
    EXPECT_HTACCESS = False

    FileCollector = StagingCollector

    def __init__(self, namespace, branch, staging_config, s3):
        # The S3 prefix for this staging site
        self.namespace = namespace
        self.branch = branch
        self.staging_config = staging_config

        self.s3 = s3
        self.collector = self.FileCollector(branch, staging_config.use_branch, namespace)

    @classmethod
    def compute_namespace(cls, prefix, username, branch, edition):
        """Staging places each stage under a unique namespace computed from an
           arbitrary username, branch, and edition. This helper returns such
           a namespace, appropriate for constructing a new Staging instance."""
        if branch in cls.RESERVED_BRANCHES:
            raise ValueError(branch)

        return '/'.join([x for x in (prefix, username, branch, edition) if x])

    def purge(self):
        """Remove all files associated with this branch and edition."""
        # Remove files from the index first; if the system dies in an
        # inconsistent state, we want to err on the side of reuploading too much
        self.collector.purge_now()

        prefix = '' if not self.namespace else '/'.join((self.namespace, ''))

        keys = [k.key for k in self.s3.list(prefix=prefix)]
        result = self.s3.delete_keys(keys)
        if result.errors:
            raise SyncException(result.errors)

    def stage(self, root):
        """Synchronize the build directory with the staging bucket under
           the namespace [username]/[branch]/[edition]/"""
        tasks = []

        redirects = {}
        htaccess_path = os.path.join(root, '.htaccess')
        try:
            if self.branch == 'master':
                redirects = translate_htaccess(htaccess_path)
        except IOError:
            # Only log an error if deploying; staging doesn't use .htaccess
            level = logging.CRITICAL if self.EXPECT_HTACCESS else logging.INFO
            LOGGER.log(level, 'Couldn\'t open required %s', htaccess_path)

            if self.EXPECT_HTACCESS:
                sys.exit(1)

        # Ensure that the root ends with a trailing slash to make future
        # manipulations more predictable.
        if not root.endswith('/'):
            root += '/'

        if not os.path.isdir(root):
            raise NoSuchEdition(root)

        # If a redirect is masking a file, we can run into an invalid 404
        # when the redirect is deleted but the file isn't republished.
        # If this is the case, warn and delete the redirect.
        for src,dest in redirects.items():
            src_path = os.path.join(root, src)
            if os.path.isfile(src_path) and os.path.basename(src_path) in os.listdir(os.path.dirname(src_path)):
                LOGGER.warn('Would ignore redirect that will mask file: %s', src)
#                del redirects[src]

        # Collect files that need to be uploaded
        for entry in self.collector.collect(root, self.s3.list(prefix=self.namespace)):
            src = entry.path.replace(root, '', 1)

            if os.path.islink(entry.path):
                # If redirecting from a directory, make sure we end it with a '/'
                suffix = self.PAGE_SUFFIX if os.path.isdir(entry.path) and not entry.path.endswith('/') else ''

                resolved = os.path.join(os.path.dirname(entry.path), os.readlink(entry.path))
                if os.path.islink(resolved):
                    LOGGER.warn('Multiple layers of symbolic link: %s', resolved)

                if not os.path.exists(resolved):
                    LOGGER.warn('Dead link: %s -> %s', entry.path, resolved)

                if not resolved.startswith(root):
                    LOGGER.warn('Skipping symbolic link %s: outside of root %s', resolved, root)

                redirects[str(Path(src + suffix).ensure_prefix(self.namespace))] = resolved.replace(root, '/', 1)
            else:
                tasks.append(functools.partial(
                    lambda path, file_hash: self.__upload(
                        path,
                        os.path.join(root, path),
                        file_hash),
                    src, entry.file_hash))

        # Run our actual staging operations in a thread pool. This would be
        # better with async IO, but this will do for now.
        LOGGER.info('Running %s tasks', len(tasks))
        run_pool(tasks)

        # XXX Right now we only sync redirects on master.
        #     Why: Master has the "canonical" .htaccess, and we'd need to attach
        #          metadata to each redirect on S3 to differentiate .htaccess
        #          redirects from symbolic links.
        #     Ramifications: Symbolic link redirects for non-master branches
        #                    will never be published.
        if self.branch == 'master':
            self.sync_redirects(redirects)

        # Remove from staging any files that our FileCollector thinks have been
        # deleted locally.
        remove_keys = [str(path.replace_prefix(root, '').ensure_prefix(self.namespace))
                       for path in [Path(p) for p in self.collector.removed_files]]

        if remove_keys:
            LOGGER.warn('Removing %s', remove_keys)
            remove_result = self.s3.delete_keys(remove_keys)
            if remove_result.errors:
                raise SyncException(remove_result.errors)

        self.collector.commit()

    def sync_redirects(self, redirects):
        """Upload the given path->url redirect mapping to the remote bucket."""
        if not redirects:
            return

        redirect_dirs = self.staging_config.redirect_dirs
        if not redirect_dirs:
            LOGGER.warn('No "redirect_dirs" listed for this project.')
            LOGGER.warn('No redirects will be removed.')

        LOGGER.info('Finding redirects to remove')
        removed = []
        remote_redirects = self.s3.list()
        for key in remote_redirects:
            # Make sure this is a redirect
            if key.size != 0:
                continue

            # Redirects are written /foo/bar/, not /foo/bar/index.html
            redirect_key = key.key.rsplit(self.PAGE_SUFFIX, 1)[0]

            # If it doesn't start with our namespace, ignore it
            if not redirect_key.startswith(self.namespace):
                continue

            # If it doesn't match one of our "owned" directories, ignore it
            if not [True for pat in redirect_dirs if pat.match(redirect_key)]:
                continue

            if redirect_key not in redirects:
                removed.append(key.key)

        LOGGER.warn('Removing %s redirects', len(removed))
        for remove in removed:
            LOGGER.warn('Removing redirect %s', remove)

        self.s3.delete_keys(removed)

        LOGGER.info('Creating %s redirects', len(redirects))
        tasks = []
        for src in redirects:
            tasks.append(functools.partial(
                    lambda src, dest, suffix: self.__redirect(
                        src + suffix,
                        dest),
                    src, redirects[src], self.PAGE_SUFFIX))
        run_pool(tasks)

    def __upload(self, local_path, src_path, file_hash):
        full_name = '/'.join((self.namespace, local_path))

        try:
            # If we don't have a hash, we can't do our normal caching stuff.
            # Just upload the file.
            if local_path in self.SHARED_CACHE_BLACKLIST or file_hash is None or not self.USE_CACHE:
                return self.__upload_nocache(src_path, full_name)

            # Try to copy the file from the cache to its destination
            file_hash = 'cache/' + binascii.b2a_hex(file_hash)

            try:
                self.s3.copy(file_hash, full_name, **self.S3_OPTIONS)
            except boto.exception.S3ResponseError as err:
                if err.status == 404:
                    # Not found in cache. Upload it to the cache
                    LOGGER.info('Uploading from %s to %s (%s)', local_path, full_name, file_hash)
                    self.s3.upload_path(src_path, file_hash, **self.S3_OPTIONS)

                    # And then copy it to its final destination
                    self.s3.copy(file_hash, full_name, **self.S3_OPTIONS)
                else:
                    raise err
        except boto.exception.S3ResponseError as err:
            raise SyncFileException(local_path, err.message)
        except IOError as err:
            LOGGER.exception('IOError while uploading file "%s": %s', local_path, err)

    def __upload_nocache(self, src_path, full_name):
        LOGGER.info('Uploading %s to %s', src_path, full_name)
        self.s3.upload_path(src_path, full_name, **self.S3_OPTIONS)

    def __redirect(self, src, dest):
        key = boto.s3.key.Key(self.s3.get_connection(), src)
        try:
            if key.get_redirect() == dest:
                LOGGER.debug('Skipping redirect %s', src)
                return
        except boto.exception.S3ResponseError as err:
            if err.status != 404:
                LOGGER.exception('S3 error creating redirect from %s to %s', src, dest)

        LOGGER.info('Redirecting %s to %s', src, dest)
        self.s3.set_redirect(key, dest)


class DeployStaging(Staging):
    PAGE_SUFFIX = '/index.html'
    USE_CACHE = False
    EXPECT_HTACCESS = True

    FileCollector = DeployCollector

    @classmethod
    def compute_namespace(cls, prefix, username, branch, edition):
        return '/'.join([x for x in (prefix, edition) if x])


def do_stage(root, staging):
    """Drive the main staging process for a single edition, and print nicer
       error messages for exceptions."""
    try:
        return staging.stage(root)
    except SyncException as err:
        LOGGER.error('Failed to upload some files:')
        for sub_err in err.errors:
            try:
                raise sub_err
            except SyncFileException:
                LOGGER.error('%s: %s', sub_err.path, sub_err.reason)
    except NoSuchEdition as err:
        LOGGER.error('No edition found at %s', err.message)
        LOGGER.info('Try specifying the -e [edition] option')


def create_config_framework(path):
    """Create a skeleton configuration file with appropriately locked-down
       permissions."""
    try:
        os.mkdir(os.path.dirname(path), 0o751)
    except OSError:
        pass

    # Make sure we don't write the framework if it already exists.
    try:
        with os.fdopen(os.open(path,
                               os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                               0o600), 'wx') as conf_file:
            conf_file.write('[authentication]\n')
    except IOError:
        pass


class StagingPipeline(object):
    Staging = Staging

    def __init__(self, args, destage, dry_run=False):
        self.args = args
        self.conf = fetch_config(args)
        self.destage = destage
        self.dry_run = dry_run

        self.branch = GitRepo().current_branch()

    def check_builder(self):
        if not self.args.builder:
            print('No builder specified. Try specifying "-b html".')
            raise ValueError(self.args.builder)

    def setup_staging_conf(self):
        self.staging_config = self.conf.deploy.get_staging(self.conf.project.name)

    def load_authentication(self):
        """Returns an AuthenticationInfo instance, or None."""
        self.cfg_path = os.path.expanduser(CONFIG_PATH)
        cfg = configparser.ConfigParser()
        cfg.read(self.cfg_path)

        # Warn the user if config permissions are too lax
        try:
            if os.name == 'posix' and stat.S_IMODE(os.stat(self.cfg_path).st_mode) != 0o600:
                LOGGER.warn('Your AWS authentication file is poorly protected! You should run')
                LOGGER.warn('    chmod 600 %s', self.cfg_path)
        except OSError:
            pass

        # Load S3 authentication information
        try:
            access_key = cfg.get('authentication', 'accesskey')
            secret_key = cfg.get('authentication', 'secretkey')
        except (configparser.NoSectionError, configparser.NoOptionError):
            print('No staging authentication found. Create a file at {0} with '
                  'contents like the following:\n'.format(self.cfg_path))
            print(SAMPLE_CONFIG)
            create_config_framework(self.cfg_path)
            return None

        # Get the user's preferred name; we use this as part of our S3 namespaces
        try:
            username = cfg.get('personal', 'username')
        except (configparser.NoSectionError, configparser.NoOptionError):
            username = pwd.getpwuid(os.getuid())[0]

        self.auth = AuthenticationInfo(access_key, secret_key, username)
        self.s3 = BulletProofS3(self.auth.access_key,
                                self.auth.secret_key,
                                self.staging_config.bucket)
        self.s3.dry_run = self.dry_run

    def setup_sourcedir(self):
        self.editions = self.args.edition or ('',)
        edition_suffixes = [self.args.builder[0] + ('-' if edition else '') + edition
                            for edition in self.editions]

        self.roots = [os.path.join(self.conf.paths.projectroot,
                              self.conf.paths.branch_output,
                              edition_suffix) for edition_suffix in edition_suffixes]

    def stage(self):
        prefix = self.staging_config.prefix

        try:
            for root, edition in zip(self.roots, self.editions):
                namespace = self.Staging.compute_namespace(prefix, self.auth.username, self.branch, edition)
                staging = self.Staging(namespace, self.branch, self.staging_config, self.s3)

                if self.destage:
                    staging.purge()
                    continue

                do_stage(root, staging)
        except boto.exception.S3ResponseError as err:
            if err.status == 403:
                LOGGER.error('Failed to upload to S3: Permission denied.')
                LOGGER.info('Check your authentication configuration at %s, '
                            'and/or talk to IT.', self.cfg_path)
                return

            raise err

    def print_report(self):
        """Print a list of staging URLs corresponding to the given editions."""
        if not self.destage:
            print('Staged at:')
            for edition in self.editions:
                suffix = '/'.join((self.auth.username, self.branch))
                if edition:
                    suffix = '{0}/{1}/{2}'.format(self.auth.username, self.branch, edition)
                print('    {0}/{1}'.format(self.staging_config.url, suffix))

    def run(self):
        self.check_builder()
        self.setup_staging_conf()
        self.load_authentication()
        self.setup_sourcedir()
        self.stage()
        self.print_report()


class DeployPipeline(StagingPipeline):
    Staging = DeployStaging

    def setup_deploy_conf(self):
        self.staging_config = self.conf.deploy.get_deploy(self.conf.project.name)

    def setup_sourcedir(self):
        self.editions = self.args.edition or ('',)
        edition_suffixes = self.editions

        self.roots = [os.path.join(self.conf.paths.projectroot,
                              self.conf.paths.public,
                              edition_suffix) for edition_suffix in edition_suffixes]

    def print_report(self):
        """Print a list of staging URLs corresponding to the given editions."""
        print('Published to:')
        print('    ' + self.staging_config.url)

    def run(self):
        # Check if the active branch is publishable. This is a sanity check
        # more than anything else, since the active branch doesn't directly
        # correlate to what is built.
        if self.branch not in self.conf.git.branches.published:
            print('Current branch ({0}) is not published'.format(self.branch))
            return

        self.check_builder()
        self.setup_deploy_conf()
        self.load_authentication()
        self.setup_sourcedir()
        self.stage()
        self.print_report()


@argh.arg('--edition', '-e', nargs='*')
@argh.arg('--destage', default=False,
          dest='_destage', help='Delete the contents of the current staged render')
@argh.arg('--builder', '-b', default='html')
@argh.arg('--dry', default=False, dest='_dry')
@argh.named('stage')
@argh.expects_obj
def main_stage(args):
    """Start an HTTP server rooted in the build directory."""
    StagingPipeline(args, destage=args._destage, dry_run=args._dry).run()


@argh.arg('--edition', '-e', nargs='*')
@argh.arg('--builder', '-b', default='html')
@argh.arg('--dry', default=False, dest='_dry')
@argh.named('s3_deploy')
@argh.expects_obj
def main_deploy(args):
    """Start an HTTP server rooted in the build directory."""
    DeployPipeline(args, destage=False, dry_run=args._dry).run()
