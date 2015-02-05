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
import libgiza.config

logger = logging.getLogger('giza.config.deploy')

class DeployConfig(libgiza.config.ConfigurationBase):
    @property
    def production(self):
        return self.state['production']

    @production.setter
    def production(self, value):
        self.state['production'] = DeployTargetConfig(value)

    @property
    def staging(self):
        return self.state['staging']

    @staging.setter
    def staging(self, value):
        self.state['staging'] = DeployTargetConfig(value)

    @property
    def testing(self):
        return self.state['testing']

    @testing.setter
    def testing(self, value):
        self.state['testing'] = DeployTargetConfig(value)

    @property
    def docsprod(self):
        return self.state['docsprod']

    @docsprod.setter
    def docsprod(self, value):
        self.state['docsprod'] = DeployTargetConfig(value)


class DeployTargetConfig(libgiza.config.ConfigurationBase):
    _option_registry = ['input']

    @property
    def args(self):
        return self.state['args']

    @args.setter
    def args(self, value):
        if isinstance(value, list):
            self.state['args'] = value
        else:
            logger.critical('deployment arguments must be a list')
            raise TypeError

    @property
    def hosts(self):
        return self.state['hosts']

    @hosts.setter
    def hosts(self, value):
        if isinstance(value, list):
            self.state['hosts'] = value
        else:
            logger.critical('deployment targets must be a list')
            raise TypeError
