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
import re
import sqlite3
import stat
import threading
import operator

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
FileUpdate = collections.namedtuple('FileUpdate', ['path', 'mtime',
                                                   'file_hash', 'is_new'])
AuthenticationInfo = collections.namedtuple('AuthenticationInfo', ['access_key', 'secret_key', 'username'])

CONFIG_PATH = '~/.config/giza-aws-authentication.conf'
SAMPLE_CONFIG = '''[authentication]
accesskey=<AWS access key>
secretkey=<AWS secret key>
'''


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


def run_pool(tasks, n_workers=50):
    """Run a list of tasks using a pool of threads. Return non-None results or
       exceptions as a list of (task, result) pairs in an arbitrary order."""
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

    return results


def translate_htaccess(path):
    """Read a .htaccess file, and transform redirects into a mapping of redirects."""
    with open(path, 'r') as f:
        data = f.read()
        return dict(REDIRECT_PAT.findall(data))


class FileCollector(object):
    """Database for detecting changed files."""
    def __init__(self, namespace, db_path):
        self.namespace = namespace
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.__init()

        self.dirty_files = []
        self.removed_files = []

    def __init(self):
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS files(
            namespace text NOT NULL,
            path text NOT NULL,
            mtime int NOT NULL,
            hash blob NOT NULL,
            PRIMARY KEY(namespace, path))''')
        cur.execute('''CREATE INDEX IF NOT EXISTS namespace ON files(namespace)''')

        cur.execute('''CREATE TEMPORARY TABLE disk(
            namespace text NOT NULL,
            path text NOT NULL,
            PRIMARY KEY(namespace, path))''')

    def collect(self, root, bucket, redirects):
        """Yield each path underneath root. Only yield files that have changed
           since the last run."""
        cur = self.conn.cursor()
        cur.execute('DELETE FROM disk')

        # Crawl symbolic links to create a distinct "realized" tree for each
        # branch, instead of using redirects. This is because Amazon uses 301
        # permanant redirects, which prevents us from juggling "manual", "master",
        # etc.
        for basedir, _, files in os.walk(root, followlinks=True):
            for filename in files:
                path = os.path.join(basedir, filename)

                # Update our temporary list of on-disk files
                cur.execute('INSERT INTO disk VALUES (?, ?)', (self.namespace, path))

                update = self.has_changed(path, bucket)
                if update is False:
                    continue

                self.dirty_files.append(update)
                yield update

        # Find files that have disappeared from the filesystem
        cur.execute('''
            SELECT path from files WHERE namespace=?
                EXCEPT
            SELECT path from disk WHERE namespace=?
            ''', (self.namespace, self.namespace))

        self.removed_files = [entry[0] for entry in cur.fetchall()]

    def has_changed(self, path, bucket):
        """Returns a FileUpdate instance if the given path has changed since it
           was last checked, or else False."""
        path_stat = os.stat(path)

        # Provide ms-level precision
        mtime = int(path_stat.st_mtime * 1000)

        cur = self.conn.cursor()
        cur.execute('SELECT * FROM files WHERE namespace=? AND path=?',
                    (self.namespace, path,))
        row = cur.fetchone()

        if row is None:
            file_hash = self.hash(path)
            update = FileUpdate(path, mtime, file_hash, True)
            return update

        if row['mtime'] == mtime:
            return False

        file_hash = self.hash(path)
        if file_hash != bytes(row['hash']):
            update = FileUpdate(path, mtime, file_hash, False)
            return update

        return False

    def commit(self):
        """Commit to cache any file changes that collect() detected. You should
           call this only once syncing is successful."""
        cur = self.conn.cursor()
        for entry in self.dirty_files:
            hash_binary_view = sqlite3.Binary(entry.file_hash)

            if entry.is_new:
                cur.execute('INSERT INTO files VALUES(?, ?, ?, ?)', (
                    self.namespace, entry.path, entry.mtime, hash_binary_view))
            else:
                cur.execute('''UPDATE files SET mtime=?, hash=?
                            WHERE namespace=? AND path=?''',
                            (entry.mtime, hash_binary_view,
                             self.namespace, entry.path))

        for path in self.removed_files:
            cur.execute('DELETE FROM disk WHERE namespace=? AND path=?',
                        (self.namespace, path))
            cur.execute('DELETE FROM files WHERE namespace=? AND path=?',
                        (self.namespace, path))

        self.conn.commit()
        self.removed_files = []

    def purge_now(self):
        """Purge the index for this namespace immediately. Does not wait for
           commit()."""
        cur = self.conn.cursor()
        cur.execute('DELETE FROM files WHERE namespace=?', (self.namespace,))
        self.conn.commit()

    @staticmethod
    def hash(path):
        """Return the cryptographic hash of the given file path as a byte
           sequence."""
        hasher = hashlib.sha256()

        with open(path, 'rb') as input_file:
            while True:
                data = input_file.read(2**13)
                if not data:
                    break

                hasher.update(data)

        return hasher.digest()


class DeployCollector(object):
    """A dummy file collector interface that always reports files as having
       changed. Yields files and all symlinks."""
    def __init__(self, namespace, db_path):
        self.removed_files = []

    def collect(self, root, bucket, redirects):
        self.removed_files = []
        remote_hashes = {}
        remote_redirects = {}
        remote_keys = bucket.list()

        # List all current redirects
        tasks = []
        for key in remote_keys:
            local_key = key.key
            if key.key.startswith('/'):
                local_key = local_key[1:]

            # Get the redirect for this key, if it exists
            if key.size == 0:
                tasks.append(functools.partial(
                    lambda key: operator.setitem(remote_redirects, key.name, key.get_redirect()),
                    key))

            # Store its MD5 hash. Might be useless if encryption or multi-part
            # uploads are used.
            remote_hashes[local_key] = key.etag.strip('"')

            if not os.path.exists(os.path.join(root, local_key)):
                self.removed_files.append(key.key)

        print('Running tasks')
        run_pool(tasks)

        for basedir, _, files in os.walk(root, followlinks=True):
            for filename in files:
                path = os.path.join(basedir, filename)
                local_hash = self.hash(path)

                remote_path = path.replace(root, '')
                if remote_hashes.get(remote_path, '') == local_hash:
                    continue

                yield self.has_changed(path, bucket)

        # # Check redirects
        # for (src, dest) in redirects.items():
        #     if key.
        #     return key.get_redirect() == dest

    def has_changed(self, path, bucket):
        return FileUpdate(path, 0, None, True)

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


class Staging(object):
    # These files are always unique, and so there is no benefit in sharing them
    SHARED_CACHE_BLACKLIST = {'genindex.html', 'objects.inv', 'searchindex.js'}

    S3_OPTIONS = {'reduced_redundancy': True}
    RESERVED_BRANCHES = {'cache'}
    PAGE_SUFFIX = ''
    USE_CACHE = True

    FileCollector = FileCollector

    def __init__(self, namespace, bucket, conf):
        # The S3 prefix for this staging site
        self.namespace = namespace

        self.bucket = bucket
        self.collector = self.FileCollector(self.namespace, conf.paths.file_changes_database)

    @classmethod
    def compute_namespace(cls, username, branch, edition):
        """Staging places each stage under a unique namespace computed from an
           arbitrary username, branch, and edition. This helper returns such
           a namespace, appropriate for constructing a new Staging instance."""
        if branch in cls.RESERVED_BRANCHES:
            raise ValueError(branch)

        return '/'.join([x for x in (username, branch, edition) if x])

    def purge(self):
        """Remove all files associated with this branch and edition."""
        # Remove files from the index first; if the system dies in an
        # inconsistent state, we want to err on the side of reuploading too much
        self.collector.purge_now()

        prefix = '' if not self.namespace else '/'.join((self.namespace, ''))

        keys = [k.key for k in self.bucket.list(prefix=prefix)]
        result = self.bucket.delete_keys(keys)
        if result.errors:
            raise SyncException(result.errors)

    def stage(self, root):
        """Synchronize the build directory with the staging bucket under
           the namespace [username]/[branch]/[edition]/"""
        tasks = []

        redirects = []
        htaccess_path = os.path.join(root, '.htaccess')
        try:
            redirects = translate_htaccess(htaccess_path)
        except IOError:
            LOGGER.error('No .htaccess found at %s', htaccess_path)

        # Ensure that the root ends with a trailing slash to make future
        # manipulations more predictable.
        if not root.endswith(os.path.sep):
            root += os.path.sep

        if not os.path.isdir(root):
            raise NoSuchEdition(root)

        for entry in self.collector.collect(root, self.bucket, redirects):
            # Run our actual staging operations in a thread pool. This would be
            # better with async IO, but this will do for now.
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

                tasks.append(functools.partial(
                    lambda src, resolved, suffix: self.__redirect(
                        src + suffix,
                        resolved.replace(root, '/', 1)),
                    src, resolved, suffix))
            else:
                tasks.append(functools.partial(
                    lambda path, file_hash: self.__upload(
                        path,
                        os.path.join(root, path),
                        file_hash),
                    src, entry.file_hash))

        # Run our sync tasks, and retry any errors
        errors = run_pool(tasks)
        errors = run_pool([result[0] for result in errors])

        if errors:
            raise SyncException([result[1] for result in errors])

        # Remove from staging any files that our FileCollector thinks have been
        # deleted locally.
        namespace_component = [self.namespace] if self.namespace else []
        remove_keys = ['/'.join(namespace_component + [path.replace(root, '', 1)])
                       for path in self.collector.removed_files]
        if remove_keys:
            LOGGER.info('Removing %s', remove_keys)
            remove_result = self.bucket.delete_keys(remove_keys)
            if remove_result.errors:
                raise SyncException(remove_result.errors)

        self.collector.commit()

    def __upload(self, local_path, src_path, file_hash):
        full_name = '/'.join((self.namespace, local_path))
        k = boto.s3.key.Key(self.bucket)

        try:
            # If we don't have a hash, we can't do our normal caching stuff.
            # Just upload the file.
            if local_path in self.SHARED_CACHE_BLACKLIST or file_hash is None or not self.USE_CACHE:
                return self.__upload_nocache(src_path, full_name)

            # Try to copy the file from the cache to its destination
            file_hash = 'cache/' + binascii.b2a_hex(file_hash)
            k.key = file_hash

            try:
                k.copy(self.bucket.name, full_name, **self.S3_OPTIONS)
            except boto.exception.S3ResponseError as err:
                if err.status == 404:
                    # Not found in cache. Upload it to the cache
                    LOGGER.info('Uploading from %s to %s (%s)', local_path, full_name, file_hash)
                    k.set_contents_from_filename(src_path, **self.S3_OPTIONS)

                    # And then copy it to its final destination
                    k.copy(self.bucket.name, full_name, **self.S3_OPTIONS)
                else:
                    raise err
        except boto.exception.S3ResponseError as err:
            raise SyncFileException(local_path, err.message)
        except IOError as err:
            LOGGER.warn('Error reading file: %s', err)

    def __upload_nocache(self, src_path, full_name):
        LOGGER.info('Uploading %s to %s', src_path, full_name)
        k = boto.s3.key.Key(self.bucket)
        k.key = full_name
        k.set_contents_from_filename(src_path, **self.S3_OPTIONS)

    def __redirect(self, src, dest):
        LOGGER.info('Redirecting %s to %s', src, dest)
        key = boto.s3.key.Key(self.bucket, src)
        key.set_redirect(dest)


class DeployStaging(Staging):
    FileCollector = DeployCollector
    PAGE_SUFFIX = '/index.html'
    USE_CACHE = False

    @classmethod
    def compute_namespace(cls, username, branch, edition):
        return ''


def do_stage(root, staging):
    """Drive the main staging process for a single edition, and print nicer
       error messages for exceptions."""
    # try:
    #     with open(os.path.join(root, '.htaccess')) as htfile:
    #         for src, dest in REDIRECT_PAT.findall(htfile.read()):
    #             if not src:
    #                 continue

    #             print(src, dest)
    #     return
    # except IOError:
    #     return

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


class StagingPipeline:
    Staging = Staging

    def __init__(self, args, destage):
        self.args = args
        self.conf = fetch_config(args)
        self.destage = destage

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
            username = os.getlogin()

        self.auth = AuthenticationInfo(access_key, secret_key, username)
        self.conn = boto.s3.connection.S3Connection(self.auth.access_key,
                                                    self.auth.secret_key)

    def setup_sourcedir(self):
        self.branch = GitRepo().current_branch()

        self.editions = self.args.edition or ('',)
        edition_suffixes = [self.args.builder[0] + ('-' if edition else '') + edition
                            for edition in self.editions]

        self.roots = [os.path.join(self.conf.paths.projectroot,
                              self.conf.paths.branch_output,
                              edition_suffix) for edition_suffix in edition_suffixes]

    def stage(self):
        try:
            bucket = self.conn.get_bucket(self.staging_config.bucket)
            for root, edition in zip(self.roots, self.editions):
                namespace = self.Staging.compute_namespace(self.auth.username, self.branch, edition)
                staging = self.Staging(namespace, bucket, self.conf)

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
        self.branch = ''
        edition_suffixes = self.editions

        self.roots = [os.path.join(self.conf.paths.projectroot,
                              self.conf.paths.public,
                              edition_suffix) for edition_suffix in edition_suffixes]

    def print_report(self):
        """Print a list of staging URLs corresponding to the given editions."""
        print('Staged at:')
        print('    ' + self.staging_config.url)

    def run(self):
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
@argh.named('stage')
@argh.expects_obj
def main_stage(args):
    """Start an HTTP server rooted in the build directory."""
    StagingPipeline(args, destage=args._destage).run()


@argh.arg('--edition', '-e', nargs='*')
@argh.arg('--builder', '-b', default='html')
@argh.named('s3_deploy')
@argh.expects_obj
def main_deploy(args):
    """Start an HTTP server rooted in the build directory."""
    DeployPipeline(args, destage=False).run()
