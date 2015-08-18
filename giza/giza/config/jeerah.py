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

import os.path
import logging

from libgiza.config import ConfigurationBase

logger = logging.getLogger('giza.config.jeerah')


class JeerahConfig(ConfigurationBase):
    @property
    def buckets(self):
        if 'buckets' in self.state:
            return self.state['buckets']
        else:
            return {}

    @property
    def site(self):
        return self.state['site']

    @site.setter
    def site(self, value):
        if isinstance(value, JeerahSiteConfig):
            self.state['site'] = value
        else:
            self.state['site'] = JeerahSiteConfig(value)

    # @property
    # def projects(self):
    #     return self.state['project']

    # @projects.setter
    # def projects(self, value):
    #     if isinstance(value, list):
    #         self.state['project'] = value
    #     else:
    #         self.state['project'] = [value]


class JeerahSiteConfig(ConfigurationBase):
    _option_registry = ['url']

    @property
    def credentials(self):
        return self.state['credentials']

    @credentials.setter
    def credentials(self, value):
        value = os.path.expanduser(value)
        self.state['credentials'] = value
