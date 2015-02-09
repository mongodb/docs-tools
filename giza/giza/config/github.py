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
import sys
import logging

from libgiza.config import ConfigurationBase
from giza.config.runtime import RuntimeStateConfigurationBase

logger = logging.getLogger('giza.config.github')

if sys.version_info >= (3, 0):
    basestring = str


def fetch_config(args):
    c = GithubConfig()
    c.ingest(args.conf_path)
    c.runstate = args

    return c


class GithubRuntimeConfig(RuntimeStateConfigurationBase):

    @property
    def conf_path(self):
        if 'conf_path' not in self.state:
            self.conf_path = None

        return self.state['conf_path']

    @conf_path.setter
    def conf_path(self, value):
        if value is not None and os.path.exists(value):
            self.state['conf_path'] = value
        else:
            try:
                self._discover_conf_file('.github.yaml')
            except OSError:
                self._discover_conf_file('github.yaml')
            except OSError:
                logger.error('could not find mdbpr github config file.')
                raise OSError


class GithubConfig(ConfigurationBase):

    @property
    def runstate(self):
        return self.state['runstate']

    @runstate.setter
    def runstate(self, value):
        if isinstance(value, GithubRuntimeConfig):
            value.conf = self
            self.state['runstate'] = value
        else:
            msg = "invalid runtime state"
            logger.critical(msg)
            raise TypeError(msg)

    @property
    def site(self):
        return self.state['site']

    @site.setter
    def site(self, value):
        if isinstance(value, GithubSiteConfig):
            self.state['site'] = value
        else:
            self.state['site'] = GithubSiteConfig(value)

    @property
    def repos(self):
        return self.state['repos']

    @repos.setter
    def repos(self, value):
        if isinstance(value, list):
            self.state['repos'] = []
            for repo in value:
                self.state['repos'].append(GithubRepoConfig(repo))
        elif isinstance(value, dict):
            if 'name' in value and 'user' in value:
                self.state['repos'].append(GithubRepoConfig(repo))
        else:
            raise TypeError('{0} is not a valid repo sepc'.format(value))

    @property
    def organizations(self):
        return self.state['organizations']

    @organizations.setter
    def organizations(self, value):
        if isinstance(value, list):
            self.state['organizations'] = value
        elif isinstance(value, basestring):
            self.state['organizations'] = [value]
        else:
            raise TypeError('{0} is not a valid organization or organization list'.format(value))

    @property
    def reporting(self):
        return self.state['reporting']

    @reporting.setter
    def reporting(self, value):
        if isinstance(value, GithubReportingConfig):
            self.state['reporting'] = value
        else:
            self.state['reporting'] = GithubReportingConfig(value)


class GithubRepoConfig(ConfigurationBase):
    _option_registry = ['user', 'name']


class GithubSiteConfig(ConfigurationBase):
    _option_registry = ['corp']

    @property
    def credentials(self):
        return self.state['credentials']

    @credentials.setter
    def credentials(self, value):
        value = os.path.expanduser(value)
        self.state['credentials'] = value


class GithubReportingConfig(ConfigurationBase):
    _option_registry = ['format']
