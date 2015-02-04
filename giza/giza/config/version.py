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

from libgiza.config import RecursiveConfigurationBase

logger = logging.getLogger('giza.config.version')

class VersionConfig(RecursiveConfigurationBase):
    _option_registry = ['release', 'branch']

    @property
    def published(self):
        if 'published' not in self.state:
            self.published = None

        return self.state['published']

    @published.setter
    def published(self, value):
        if 'version' in self.conf.runstate.branch_conf and 'published' in self.conf.runstate.branch_conf['version']:
            p = self.conf.runstate.branch_conf['version']['published']

            if not isinstance(p, list):
                msg = "published branches must be a list"
                logger.critical(msg)
                raise TypeError(msg)

            self.state['published'] = p
        else:
            self.state['published'] = []

    @property
    def upcoming(self):
        if 'upcoming' not in self.state:
            self.upcoming = None

        return self.state['upcoming']

    @upcoming.setter
    def upcoming(self, value):
        if 'version' in self.conf.runstate.branch_conf and 'upcoming' in self.conf.runstate.branch_conf['version']:
            self.state['upcoming'] = self.conf.runstate.branch_conf['version']['upcoming']
        else:
            self.state['upcoming'] = None

    @property
    def stable(self):
        if 'stable' not in self.state:
            self.stable = None

        return self.state['stable']

    @stable.setter
    def stable(self, value):
        if 'version' in self.conf.runstate.branch_conf and 'stable' in self.conf.runstate.branch_conf['version']:
            self.state['stable'] = self.conf.runstate.branch_conf['version']['stable']
        else:
            self.state['stable'] = None
