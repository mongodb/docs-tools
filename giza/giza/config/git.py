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

import logging
import os

from libgiza.git import GitRepo
from libgiza.config import RecursiveConfigurationBase, ConfigurationBase

logger = logging.getLogger('giza.config.git')


class GitConfigBase(RecursiveConfigurationBase):
    def __init__(self, obj, conf, repo=None):
        super(GitConfigBase, self).__init__(obj, conf)
        self.repo = repo

    @property
    def repo(self):
        return self._repo

    @repo.setter
    def repo(self, path=None):
        if isinstance(path, GitRepo):
            self._repo = path
        elif path is None:
            self._repo = GitRepo(self.conf.paths.projectroot)
        elif os.path.isdir(path):
            self._repo = GitRepo(path)
        else:
            self._repo = GitRepo(os.getcwd())


class GitConfig(GitConfigBase):
    @property
    def commit(self):
        c = self.repo.sha('HEAD')
        self.state['commit'] = c
        return c

    @property
    def branches(self):
        if 'branches' not in self.state:
            self.branches = None
        return self.state['branches']

    @branches.setter
    def branches(self, value):
        self.state['branches'] = GitBranchConfig(None, self.conf, self.repo)

    @property
    def remote(self):
        if 'remote' not in self.state:
            self.remote = None
        return self.state['remote']

    @remote.setter
    def remote(self, value):
        self.state['remote'] = GitRemoteConfig(value)


class GitBranchConfig(GitConfigBase):

    @property
    def current(self):
        if 'current' not in self.state:
            self.current = None

        return self.state['current']

    @current.setter
    def current(self, value):
        self.state['current'] = self.repo.current_branch()

    @property
    def manual(self):
        if 'manual' not in self.state:
            self.manual = None

        return self.state['manual']

    @manual.setter
    def manual(self, value):
        if self.has_branches() is True:
            if 'manual' in self.conf.runstate.branch_conf['git']['branches']:
                self.state['manual'] = self.conf.runstate.branch_conf['git']['branches']['manual']
            else:
                self.state['manual'] = None
        else:
            self.state['manual'] = None

    @property
    def published(self):
        if 'published' not in self.state:
            self.published = None

        return self.state['published']

    def has_branches(self):
        return ('git' in self.conf.runstate.branch_conf and
                'branches' in self.conf.runstate.branch_conf['git'])

    @published.setter
    def published(self, value):
        if self.has_branches() is True:
            if 'published' in self.conf.runstate.branch_conf['git']['branches']:
                p = self.conf.runstate.branch_conf['git']['branches']['published']

                if not isinstance(p, list):
                    msg = "published branches must be a list"
                    logger.critical(msg)
                    raise TypeError(msg)
                elif p[0] != 'master':
                    msg = "right now, we must publish master"
                    logger.critical(msg)
                    raise TypeError(msg)

                self.state['published'] = p

            else:
                self.state['published'] = []
        else:
            self.state['published'] = ['master']


class GitRemoteConfig(ConfigurationBase):
    _option_registry = ['upstream', 'tools']
