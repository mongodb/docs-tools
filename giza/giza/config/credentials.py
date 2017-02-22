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

from giza.libgiza.config import ConfigurationBase

logger = logging.getLogger('giza.config.credentials')


def get_credentials_skeleton():
    return {
        'jira': {
            'username': None,
            'password': None,
            'url': None,
        },
        'corp': {
            'username': None,
            'password': None,
            'seed': None,
        },
        'github': {
            'username': None,
            'password': None,
            'token': None,
        },
        'aws': {
            'key': None,
            'secret': None
        },
        's3': {
            'key': None,
            'secret': None
        }
    }


class CredentialsConfig(ConfigurationBase):
    _option_registry = []

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

    @property
    def aws(self):
        return self.state['aws']

    @aws.setter
    def aws(self, value):
        self.state['aws'] = AwsCredentialsConfig(value)

    @property
    def s3(self):
        return self.state['s3']

    @s3.setter
    def s3(self, value):
        self.state['s3'] = AwsCredentialsConfig(value)

    @property
    def rhn(self):
        return self.state['rhn']

    @rhn.setter
    def rhn(self, value):
        self.state['rhn'] = RhnCredentialsConfig(value)


class JiraCredentialsConfig(ConfigurationBase):
    _option_registry = ['username', 'password']

    @property
    def url(self):
        if 'url' in self.state:
            return self.state['url']
        else:
            logger.error("jira url is not specified.")
            return ""

    @url.setter
    def url(self, value):
        value = value.strip()

        if value.startswith('http'):
            self.state['url'] = value
            if value[4] != 's':
                logger.warning("jira url is not https.")
        else:
            logger.error("invalid jira url")
            raise TypeError


class CorpCredentialsConfig(ConfigurationBase):
    _option_registry = ['username', 'password', 'seed']


class GithubCredentialsConfig(ConfigurationBase):
    _option_registry = ['username', 'password', 'token']


class AwsCredentialsConfig(ConfigurationBase):
    _option_registry = ['key', 'secret']


class RhnCredentialsConfig(ConfigurationBase):
    _option_registry = ['username', 'password']
