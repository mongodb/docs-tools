# Copyright 2014 MongoDB, Inc.
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

"""
Provides the :class:`~giza.git.GitRepo()` class that provides a thin
Python-layer on top of common git operations.
"""

import logging
import os
import re
import sys
import contextlib
import subprocess
import shlex

logger = logging.getLogger('giza.libgiza.git')

if sys.version_info >= (3, 0):
    basestring = str

    def unicode(s):
        return str(s, 'utf-8')


class GitError(Exception):
    pass


class GitRepo(object):
    """
    An object that represents a git repository, and provides methods to wrap
    many common git commands and basic aggregate operations.
    """

    def __init__(self, path=None):
        """
        :param string path: Optional. Defines a the path of the git
           repository. If not specified, defaults to the current working
           directory.

           Attempts to find the top-level (root) directory of the git
           repository, if you specify a path that's a sub-directory in a git
           repository.
        """

        if path is None:
            self.path = os.getcwd()
        else:
            self.path = path

        logger.debug("created git repository management object for {0}".format(self.path))

    def cmd(self, *args):
        cmd_parts = ['git']

        for arg in args:
            if isinstance(arg, list):
                cmd_parts.extend(arg)
            else:
                cmd_parts.append(arg)

        try:
            if os.path.exists(self.path):
                logger.debug("running git command ({0}) at path {1}".format(' '.join(cmd_parts),
                                                                            self.path))
                return unicode(subprocess.check_output(args=cmd_parts,
                                                       cwd=self.path,
                                                       stderr=subprocess.STDOUT).strip())
            else:
                logger.debug("running git command: " + ' '.join(cmd_parts))
                return unicode(subprocess.check_output(args=cmd_parts,
                                                       stderr=subprocess.STDOUT).strip())

        except Exception as e:
            raise GitError('encountered error {0} ({1}) with {2} in repository '
                           '{3}'.format(e, type(e), ' '.join(cmd_parts), self.path))

    def clone(self, remote, repo_path=None, branch=None, depth=None):
        args = ['clone', remote]

        if branch is not None:
            args.extend(['--branch', branch])

        if depth is not None:
            if isinstance(depth, int):
                depth = str(int)
            args.extend(["--depth", depth])

        if repo_path is not None:
            args.append(repo_path)
            self.path = repo_path

        ret = self.cmd(*args)

        return ret

    def create_repo(self, bare=False):
        args = ['init']

        if bare is True:
            args.append('--bare')

        return self.cmd(*args)

    def top_level(self):
        try:
            return self.cmd('rev-parse', '--show-toplevel')
        except GitError:
            logger.error('{0} may not be a git repository'.format(self.path))
            return self.path

    def is_repository(self):
        if os.path.isdir(os.path.join(self.top_level(), ".git")):
            return True
        else:
            return False

    def remotes(self):
        return self.cmd('remote').split('\n')

    def author_email(self, sha=None):
        if sha is None:
            sha = self.sha()

        return self.cmd('log', shlex.split(sha + '~..' + sha + " --pretty='format:%ae'"))

    def branch_exists(self, name):
        r = self.cmd('branch', '--list', name).split('\n')
        if '' in r:
            r.remove('')

        if name in r:
            return True
        else:
            return False

    def branch_file(self, path, branch='master'):
        return self.cmd('show', ':'.join((branch, path)))

    def checkout(self, ref):
        self.cmd('checkout', ref)
        return True

    def create_branch(self, name, tracking=None):
        args = ['branch', name]

        if tracking is not None:
            args.append(tracking)

        return self.cmd(*args)

    def checkout_branch(self, name, tracking=None):
        if self.current_branch() == name:
            return

        args = ['checkout']

        if not self.branch_exists(name):
            args.append('-b')

        args.append(name)

        if tracking is not None:
            args.append(tracking)

        return self.cmd(*args)

    def remove_branch(self, name, force=False):
        args = ['branch']

        if force is False:
            args.append('-d')
        else:
            args.append('-D')

        args.append(name)

        return self.cmd(*args)

    def rebase(self, onto):
        return self.cmd('rebase', onto)

    def merge(self, branch):
        return self.cmd('merge', branch)

    def hard_reset(self, ref='HEAD'):
        return self.cmd('reset', '--hard', ref)

    def reset(self, ref='HEAD'):
        return self.cmd('reset', ref)

    def fetch(self, remote='origin'):
        return self.cmd('fetch', remote)

    def fetch_all(self):
        return self.cmd('fetch', '--all')

    def update(self):
        return self.cmd('pull', '--rebase')

    def pull(self, remote='origin', branch='master'):
        return self.cmd('pull', remote, branch)

    def push(self, remote='origin', ref=None):
        if ref is None:
            ref = self.current_branch()

        return self.cmd("push", remote, ref)

    def tag(self, name, ref="HEAD", annotation=None, delete=False, force=False):
        args = ["tag"]

        if delete is True:
            args.append("-d")

        if force is True:
            args.append("-f")

        if annotation is not None:
            if isinstance(annotation, basestring):
                args.extend(["-m", annotation])
            else:
                raise TypeError("tag annotations must be strings. {0} {1} "
                                "is not a string".format(annotation, type(annotation)))

        args.extend([name, ref])

        return self.cmd(*args)

    def is_tagged(self, name, ref="HEAD", lightweight=False):
        cmd = ["describe"]

        if lightweight is True:
            cmd.append("--tags")

        cmd.append(name)

        try:
            self.cmd(*cmd)
        except GitError:
            return False

        if ref == "HEAD":
            ref = self.sha(ref)

        tagged_commit = self.cmd(["rev-list", "-n", "1", name])
        if tagged_commit == ref:
            return True
        else:
            return False

    def current_branch(self):
        return self.cmd('symbolic-ref', 'HEAD').split('/')[2]

    def sha(self, ref='HEAD'):
        return self.cmd('rev-parse', '--verify', ref)

    def commit_messages(self, num=1):
        args = ['log', '--oneline', '--max-count=' + str(num)]
        log = self.cmd(*args)

        return [' '.join(m.split(' ')[1:])
                for m in log.split('\n')]

    def cherry_pick(self, *args):
        if len(args) == 1:
            args = args[0]

        for commit in args:
            self.cmd('cherry-pick', commit)
            logger.info('cherry picked ' + commit)

    def am(self, patches, repo=None, sign=False):
        cmd_base = 'curl -s {path} | git am --3way'

        if sign is True:
            cmd_base += ' --signoff'

        for obj in patches:
            if obj.startswith('http'):
                path = obj
                if not obj.endswith('.patch'):
                    path = obj + '.patch'

                logger.info("applying {0}".format(path))
            elif re.search('[a-zA-Z]+', obj):
                path = '/'.join([repo, 'commit', obj]) + '.patch'

                logger.info('merging {0} for {1} into {2}'.format(obj, repo, self.current_branch()))
            else:
                if repo is None:
                    logger.warning('not applying "{0}", because of missing repo'.format(obj))
                    continue
                else:
                    path = '/'.join([repo, 'pull', obj]) + '.patch'
                    logger.info("applying {0}".format(path))

            logger.info(cmd_base.format(path=path))
            subprocess.call(cwd=self.path,
                            args=cmd_base.format(path=path),
                            stderr=subprocess.STDOUT,
                            shell=True)

    @contextlib.contextmanager
    def branch(self, name):
        starting_branch = self.current_branch()

        if name != starting_branch:
            self.checkout(name)

        yield

        if name != starting_branch:
            self.checkout(starting_branch)
