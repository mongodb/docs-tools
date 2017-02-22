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

import os
import logging
import contextlib

logger = logging.getLogger('giza.libgit')

try:
    import pygit2
except ImportError:
    pygit2 = None
    import giza.libgiza.git


class GitError(Exception):
    pass


class GitRepo(object):
    def __init__(self, path=None):
        """
        :param string path: Optional. Defines a the path of the git
           repository. If not specified, defaults to the current working
           directory.
        """
        if pygit2 is None:
            logger.warning("without pylibgit2 installed, falling back "
                           "to wrapped git repo implementation.")
            return giza.libgiza.git.GitRepo(path)

        if path is None:
            self.path = os.getcwd()
        else:
            self.path = path

        self.path = pygit2.discover_repository(self.path)
        self.repo = pygit2.Repository(self.path)

        logger.debug("created git repository management object for {0}".format(self.path))

    def cmd(self, *args):
        raise NotImplementedError

    def remotes(self):
        return [r.name for r in self.repo.remotes]

    def author_email(self, sha=None):
        commit = self.repo.get(sha, None)

        if commit is None or not isinstance(commit, pygit2.Commit):
            return ""
        else:
            return commit.author

    def branch_exists(self, name):
        return name in self.repo.listall_branches()

    def branch_file(self, path, branch="master"):
        ref = self.repo.lookup_branch(branch)
        head = self.repo.lookup_reference(ref.name)
        commit = self.repo.get(head.target)

        return self.repo[commit.tree[path].id]

    def checkout(self, ref):
        self.repo.checkout(refnmae=ref)

        return True

    def checkout_branch(self, name, tracking=None):
        pass

    def remote_branch(self, name, force=False):
        pass

    def rebase(self, onto):
        pass

    def merge(self, branch):
        pass

    def hard_reset(self, ref='head'):
        pass

    def fetch(self, remote='origin'):
        pass

    def update(self):
        pass

    def pull(self, remote='origin', branch='master'):
        pass

    def current_branch(self):
        pass

    def sha(self, ref='HEAD'):
        pass

    def clone(self, remote, repo_path=None, branch=None):
        pass

    def am(self, patches, repo=None, sign=False):
        pass

    @contextlib.contextmanager
    def branch(self, name):
        pass
