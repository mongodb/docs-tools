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

import time
import binascii
import collections
import hashlib
import logging
import os
import os.path
import sqlite3
import stat

import argh
import boto.s3.connection
import boto.s3.bucket
import boto.s3.key
import boto.s3.lifecycle

import libgiza.app
import libgiza.task
import libgiza.git

from giza.config.helper import fetch_config

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

logger = logging.getLogger('giza.operations.stage')

FileUpdate = collections.namedtuple('FileUpdate', ['path', 'mtime',
                                                   'file_hash', 'is_new'])

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

    def collect(self, root):
        """Yield each path underneath root. Only yield files that have changed
           since the last run."""
        cur = self.conn.cursor()
        cur.execute('DELETE FROM disk')

        for basedir, _, files in os.walk(root):
            for filename in files:
                path = os.path.join(basedir, filename)

                # Update our temporary list of on-disk files
                cur.execute('INSERT INTO disk VALUES (?, ?)', (self.namespace, path))

                update = self.has_changed(path)
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

        removed_files = [entry[0] for entry in cur.fetchall()]
        self.removed_files.extend(removed_files)

    def has_changed(self, path):
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
        """Return the SHA-256 hash of the given file path as a byte sequence."""
        hasher = hashlib.sha256()

        with open(path, 'rb') as input_file:
            while True:
                data = input_file.read(2**13)
                if not data:
                    break

                hasher.update(data)

        return hasher.digest()


class Staging(object):
    # These files are always unique, and so there is no benefit in sharing them
    SHARED_CACHE_BLACKLIST = {'genindex.html', 'objects.inv', 'searchindex.js'}

    S3_OPTIONS = {'reduced_redundancy': True}
    RESERVED_BRANCHES = {'cache'}

    def __init__(self, namespace, bucket, conf):
        # The S3 prefix for this staging site
        self.namespace = namespace
        self.conf = conf
        self.bucket = bucket

        self.collector = FileCollector(self.namespace, self.conf.paths.file_changes_database)

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

        keys = [k.key for k in self.bucket.list(prefix='/'.join((self.namespace, '')))]
        result = self.bucket.delete_keys(keys)
        if result.errors:
            raise SyncException(result.errors)

    def stage(self, root):
        """Synchronize the build directory with the staging bucket under
           the namespace [username]/[branch]/[edition]/"""
        # Ensure that the root ends with a trailing slash to make future
        # manipulations more predictable.
        if not root.endswith(os.path.sep):
            root += os.path.sep

        if not os.path.isdir(root):
            raise NoSuchEdition(root)

        with libgiza.app.BuildApp.new(pool_type="threads",
                                      pool_size=50,
                                      force=self.conf.runstate.force).context() as app:
            for entry in self.collector.collect(root):
                # Run our actual staging operations in a thread pool. This would be
                # better with async IO, but this will do for now.
                path = entry.path.replace(root, '', 1)

                message = "task to upload {0} to S3 ".format(path)
                app.add(task=libgiza.task.Task(job=_upload_file_to_s3,
                                               args={'local_path': path,
                                                     'src_path': os.path.join(root, path),
                                                     'file_hash': entry.file_hash,
                                                     'namespace': self.namespace,
                                                     'bucket': self.bucket},
                                               description=message,
                                               dependency=path,
                                               target=True))

        # all tasks in the app execute when we clean up from the context
        # manager.

        # Remove from staging any files that our FileCollector thinks have been
        # deleted locally.
        remove_keys = ['/'.join((self.namespace, path.replace(root, '', 1)))
                       for path in self.collector.removed_files]
        if remove_keys:
            logger.info('Removing %s', remove_keys)
            remove_result = self.bucket.delete_keys(remove_keys)
            if remove_result.errors:
                raise SyncException(remove_result.errors)

        self.collector.commit()

        return


def _upload_file_to_s3(local_path, src_path, file_hash, namespace, bucket, should_retry=False):
    full_name = '/'.join((namespace, local_path))
    k = boto.s3.key.Key(bucket)

    try:
        if local_path in Staging.SHARED_CACHE_BLACKLIST:
            logger.info('Uploading %s', local_path)
            k.key = full_name
            k.set_contents_from_filename(src_path, **Staging.S3_OPTIONS)
            return None

        # Try to copy the file from the cache to its destination
        file_hash = 'cache/' + binascii.b2a_hex(file_hash)
        k.key = file_hash

        try:
            k.copy(bucket.name, full_name, **Staging.S3_OPTIONS)
        except boto.exception.S3ResponseError as err:
            if err.status == 404:
                # Not found in cache. Upload it to the cache
                logger.info('Uploading %s', local_path)
                k.set_contents_from_filename(src_path, **Staging.S3_OPTIONS)

                # And then copy it to its final destination
                k.copy(bucket.name, full_name, **Staging.S3_OPTIONS)
            else:
                raise err
    except boto.exception.S3ResponseError as err:
        if should_retry is True:
            logger.warning("encountered error uploading {0}, retrying once in a bit.".format())
            time.sleep(0.25)
            _upload_file_to_s3(local_path, src_path, file_hash, namespace, bucket, False)
        else:
            raise SyncFileException(local_path, err.message)


def do_stage(root, staging):
    """Drive the main staging process for a single edition, and print nicer
       error messages for exceptions."""
    try:
        return staging.stage(root)
    except SyncException as err:
        logger.error('Failed to upload some files:')
        for sub_err in err.errors:
            try:
                raise sub_err
            except SyncFileException:
                logger.error('%s: %s', sub_err.path, sub_err.reason)
    except NoSuchEdition as err:
        logger.error('No edition found at %s', err.message)
        logger.info('Try specifying the -e [edition] option')


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


def print_stage_report(url, username, branch, editions):
    """Print a list of staging URLs corresponding to the given editions."""
    print('Staged at:')
    for edition in editions:
        suffix = '/'.join((username, branch))
        if edition:
            suffix = '{0}/{1}/{2}'.format(username, branch, edition)
        print('    {0}/{1}'.format(url, suffix))


@argh.arg('--edition', '-e', nargs='*')
@argh.arg('--destage', default=False,
          dest='_destage', help='Delete the contents of the current staged render')
@argh.arg('--builder', '-b', default='html')
@argh.named('stage')
@argh.expects_obj
def main(args):
    """Start an HTTP server rooted in the build directory."""
    conf = fetch_config(args)
    staging_config = conf.deploy.get_staging(conf.project.name)

    branch = libgiza.git.GitRepo().current_branch()

    cfg_path = os.path.expanduser(CONFIG_PATH)
    cfg = configparser.ConfigParser()
    cfg.read(cfg_path)

    # Warn the user if file permissions are too lax
    try:
        if os.name == 'posix' and stat.S_IMODE(os.stat(cfg_path).st_mode) != 0o600:
            logger.warn('Your AWS authentication file is poorly protected! You should run')
            logger.warn('    chmod 600 %s', cfg_path)
    except OSError:
        pass

    try:
        access_key = cfg.get('authentication', 'accesskey')
        secret_key = cfg.get('authentication', 'secretkey')
    except (configparser.NoSectionError, configparser.NoOptionError):
        print('No staging authentication found. Create a file at {0} with '
              'contents like the following:\n'.format(cfg_path))
        print(SAMPLE_CONFIG)
        create_config_framework(cfg_path)
        return

    try:
        username = cfg.get('personal', 'username')
    except (configparser.NoSectionError, configparser.NoOptionError):
        username = os.getlogin()

    if not args.builder:
        print('No builder specified. Try specifying "-b html".')
        return

    editions = args.edition or ('',)
    edition_suffixes = [args.builder[0] + ('-' if edition else '') + edition
                        for edition in editions]

    roots = [os.path.join(conf.paths.projectroot,
                          conf.paths.branch_output,
                          edition_suffix) for edition_suffix in edition_suffixes]

    conn = boto.s3.connection.S3Connection(access_key, secret_key)

    try:
        bucket = conn.get_bucket(staging_config.bucket)
        for root, edition in zip(roots, editions):
            namespace = Staging.compute_namespace(username, branch, edition)
            staging = Staging(namespace, bucket, conf)

            if args._destage:
                staging.purge()
                continue

            do_stage(root, staging)
    except boto.exception.S3ResponseError as err:
        if err.status == 403:
            logger.error('Failed to upload to S3: Permission denied.')
            logger.info('Check your authentication configuration at %s, '
                        'and/or talk to IT.', cfg_path)
            return

    if not args._destage:
        print_stage_report(staging_config.url, username, branch, editions)
