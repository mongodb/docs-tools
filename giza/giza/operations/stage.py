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
import sqlite3
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


class DeleteException(StagingException):
    """An exception indicating an S3 deletion error."""
    def __init__(self, errors):
        StagingException.__init__(self, 'Error deleting keys')
        self.errors = errors


class PoolWorker(threading.Thread):
    """A threaded worker that works on a queue of functions."""
    def __init__(self, **kwargs):
        threading.Thread.__init__(self, **kwargs)

        # Avoid needing to mutex-protect this queue by only ever appending to it
        self.tasks = []
        self.i = 0

        self.semaphore = threading.Semaphore(0)

    def run(self):
        while True:
            self.semaphore.acquire()

            next_task = self.tasks[self.i]
            if next_task is None:
                return

            next_task()
            self.i += 1

    def add_task(self, task):
        """Adds a function to this work queue. The worker will exit if it
           reaches a None value."""
        self.tasks.append(task)
        self.semaphore.release()


def run_pool(tasks, n_workers=100):
    """Run a list of tasks using a pool of threads."""
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


class FileCollector:
    """Database for detecting changed files."""
    def __init__(self, branch):
        self.branch = branch
        self.conn = sqlite3.connect('.stage-cache.db')
        self.conn.row_factory = sqlite3.Row
        self.__init()

        self.dirty_files = []
        self.removed_files = []

    def __init(self):
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS files(
            branch text NOT NULL,
            path text NOT NULL,
            mtime int NOT NULL,
            hash blob NOT NULL,
            PRIMARY KEY(branch, path))''')
        cur.execute('''CREATE INDEX IF NOT EXISTS branch ON files(branch)''')

        cur.execute('''CREATE TEMPORARY TABLE disk(
            branch text NOT NULL,
            path text NOT NULL,
            PRIMARY KEY(branch, path))''')

    def collect(self, root):
        """Yield each path underneath root. If incremental is True, then only
           yield files that have changed since the last run."""
        cur = self.conn.cursor()
        cur.execute('DELETE FROM disk')

        for basedir, _, files in os.walk(root):
            for filename in files:
                path = os.path.join(basedir, filename)

                # Update our temporary list of on-disk files
                cur.execute('INSERT INTO disk VALUES (?, ?)', (self.branch, path))

                update = self.has_changed(path)
                if update is False:
                    continue

                self.dirty_files.append(update)
                yield update

        # Find files that have disappeared from the filesystem
        cur.execute('''
            SELECT path from files WHERE branch=?
                EXCEPT
            SELECT path from disk WHERE branch=?
            ''', (self.branch, self.branch))

        removed_files = [entry[0] for entry in cur.fetchall()]
        self.removed_files.extend(removed_files)

    def has_changed(self, path):
        """Returns a FileUpdate instance if the given path has changed since it
           was last checked, or else False."""
        stat = os.stat(path)

        # Provide ms-level precision
        mtime = int(stat.st_mtime * 1000)

        cur = self.conn.cursor()
        cur.execute('SELECT * FROM files WHERE branch=? AND path=?',
                    (self.branch, path,))
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
                    self.branch, entry.path, entry.mtime, hash_binary_view))
            else:
                cur.execute('''UPDATE files SET mtime=?, hash=?
                            WHERE branch=? AND path=?''',
                            (entry.mtime, hash_binary_view,
                             self.branch, entry.path))

        for path in self.removed_files:
            cur.execute('DELETE FROM disk WHERE branch=? AND path=?',
                        (self.branch, path))
            cur.execute('DELETE FROM files WHERE branch=? AND path=?',
                        (self.branch, path))

        self.conn.commit()
        self.removed_files = []

    def purge_now(self):
        """Purge the index for this branch immediately. Does not wait for
           commit()."""
        cur = self.conn.cursor()
        cur.execute('DELETE FROM files WHERE branch=?', (self.branch,))
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


class Staging:
    # These files are always unique, and so there is no benefit in sharing them
    SHARED_CACHE_BLACKLIST = {'genindex.html', 'objects.inv', 'searchindex.js'}

    S3_OPTIONS = {'reduced_redundancy': True}

    def __init__(self, branch, bucket):
        self.branch = branch
        self.bucket = bucket
        self.collector = FileCollector(branch)

        # Check this bucket's expiration policy
        try:
            bucket.get_lifecycle_config()
        except boto.exception.S3ResponseError:
            lifecycle = boto.s3.lifecycle.Lifecycle()
            lifecycle.add_rule(
                'staging-expiration',
                status='Enabled',
                expiration=boto.s3.lifecycle.Expiration(30))
            bucket.configure_lifecycle(lifecycle)

    def purge(self):
        """Remove all files associated with this branch."""
        # Remove files from the index first; if the system dies in an
        # inconsistent state, we want to err on the side of reuploading too much
        self.collector.purge_now()

        keys = [k.key for k in self.bucket.list(prefix=self.branch + '/')]
        result = self.bucket.delete_keys(keys)
        if result.errors:
            raise DeleteException(result.errors)

    def stage(self, root, incremental=True):
        """Synchronize the build directory with the staging bucket."""
        tasks = []

        # Ensure that the root ends with a trailing slash to make future
        # manipulations more predictable.
        if not root.endswith(os.path.sep):
            root += os.path.sep

        if not incremental:
            self.purge()

        for entry in self.collector.collect(root):
            # Run our actual staging operations in a thread pool. This would be
            # better with async IO, but this will do for now.
            path = entry.path.replace(root, '', 1)
            tasks.append(functools.partial(
                lambda path, file_hash: self.__upload(
                    path,
                    os.path.join(root, path),
                    file_hash),
                path, entry.file_hash))

        run_pool(tasks)

        # Remove from staging any files that our FileCollector thinks have been
        # deleted locally.
        remove_keys = [os.path.join(self.branch, path.replace(root, '', 1))
                       for path in self.collector.removed_files]
        if remove_keys:
            LOGGER.info('Removing %s', remove_keys)
            remove_result = self.bucket.delete_keys(remove_keys)
            if remove_result.errors:
                raise DeleteException(remove_result.errors)

        self.collector.commit()

    def __upload(self, local_path, src_path, file_hash):
        LOGGER.info('Uploading %s', local_path)
        full_name = os.path.join(self.branch, local_path)

        if local_path in self.SHARED_CACHE_BLACKLIST:
            k = boto.s3.key.Key(self.bucket)
            k.key = full_name
            k.set_contents_from_filename(src_path, **self.S3_OPTIONS)
            return None

        file_hash = binascii.b2a_hex(file_hash)
        k = self.bucket.get_key(file_hash)
        if k is None:
            k = boto.s3.key.Key(self.bucket)
            k.key = file_hash
            k.set_contents_from_filename(src_path, **self.S3_OPTIONS)

        k.copy(self.bucket.name, full_name, **self.S3_OPTIONS)


@argh.arg('--edition', '-e')
@argh.arg('--destage', default=False,
          dest='destage', help='Delete the contents of the current staged render')
@argh.arg('--incremental', default=True,
          dest='incremental', help='Intelligently update the stage')
@argh.arg('--builder', '-b', nargs='*', default='html')
@argh.named('stage')
@argh.expects_obj
def start(args):
    """Start an HTTP server rooted in the build directory."""
    conf = fetch_config(args)

    git = GitRepo()
    branch = git.current_branch()

    cfg = configparser.ConfigParser()
    cfg.read(os.path.expanduser(CONFIG_PATH))

    try:
        access_key = cfg.get('authentication', 'accesskey')
        secret_key = cfg.get('authentication', 'secretkey')
    except configparser.NoSectionError:
        print('No staging authentication found. Create a file at {0} with '
              'contents like the following:\n'.format(CONFIG_PATH))
        print(SAMPLE_CONFIG)
        return

    root = conf.paths.public_site_output

    if conf.runstate.edition is not None:
        root = os.path.join(conf.paths.projectroot,
                            conf.paths.branch_output,
                            '-'.join((args.builder[0], args.edition)))
    else:
        root = os.path.join(conf.paths.projectroot,
                            conf.paths.branch_output,
                            args.builder[0])

    conn = boto.s3.connection.S3Connection(access_key, secret_key)
    bucket = conn.get_bucket(conf.project.stagingbucket)
    staging = Staging(branch, bucket)

    if conf.runstate.destage:
        staging.purge()
        return

    staging.stage(root, incremental=conf.runstate.incremental)
