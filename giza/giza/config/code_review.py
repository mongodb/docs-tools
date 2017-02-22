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

import collections
import logging

import giza.libgiza.config

logger = logging.getLogger('giza.config.code_review')


class CodeReviewConfiguration(giza.libgiza.config.ConfigurationBase):
    _version = 1

    @property
    def v(self):
        if 'v' not in self.state:
            return self._version
        else:
            return self.state['v']

    @v.setter
    def v(self, value):
        if 'v' >= self._version:
            self.state['v'] = value
        else:
            self.state['v'] = self._version

    @property
    def branches(self):
        if 'branches' in self.state:
            return self.state['branches']
        else:
            return {}

    @branches.setter
    def branches(self, value):
        if not isinstance(value, dict):
            raise TypeError

        if isinstance(value, list):
            for item in value:
                if len(item) != 2:
                    raise TypeError
            branches = value
        elif isinstance(value, dict):
            branches = value.items()

        for k, v in branches:
            self.set_branch(k, v)

    def set_branch(self, name, branch):
        if 'branches' not in self.state:
            self.state['branches'] = {}

        if isinstance(branch, CodeReviewBranchConfiguration):
            self.state['branches'][name] = branch
        elif isinstance(name, dict):
            self.state['branches'][name] = CodeReviewBranchConfiguration(branch)
        else:
            try:
                self.state['branches'][name] = CodeReviewBranchConfiguration(dict(branch))
            except:
                m = "{0} is not a valid configuration branch object: {1}".format(name, branch)
                logger.error(m)

    def get_branch(self, branch):
        if 'branches' not in self.state or branch not in self.state['branches']:
            self.state['branches'][branch] = CodeReviewBranchConfiguration()

        return self.state['branches'][branch]


class CodeReviewBranchConfiguration(giza.libgiza.config.ConfigurationBase):
    _option_registry = ['original_name', 'issue']

    @property
    def commits(self):
        if 'commits' in self.state:
            return self.state['commits']
        else:
            return []

    @commits.setter
    def commits(self, value):
        if 'commits' not in self.state:
            if isinstance(value, list):
                self.state['commits'] = value
            elif isinstance(value, collections.Iterable):
                self.state['commits'] = list(value)
            else:
                raise TypeError
        else:
            if isinstance(value, collections.Iterable):
                self.state['commits'].extend(value)
            else:
                self.state['commits'].append(value)
