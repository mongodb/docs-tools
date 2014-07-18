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

logger = logging.getLogger('giza.config.credentials')

from giza.config.base import ConfigurationBase

class CredentialsConfig(ConfigurationBase):
    @property
    def jira(self):
        return self.state['jira']

    @jira.setter
    def jira(self, value):
        self.state['jira'] = JiraCredentialsConfig(value)

    @property
    def corp(self):
        return self.state['corp']

    @corp.setter
    def corp(self, value):
        self.state['corp'] = CorpCredentialsConfig(value)

    @property
    def github(self):
        return self.state['github']

    @github.setter
    def github(self, value):
        self.state['github'] = GithubCredentialsConfig(value)

class JiraCredentialsConfig(ConfigurationBase):
    _option_registry = [ 'username', 'password' ]

class CorpCredentialsConfig(ConfigurationBase):
    _option_registry = [ 'username', 'password' ]

class GithubCredentialsConfig(ConfigurationBase):
    _option_registry = [ 'username', 'password', 'token' ]
