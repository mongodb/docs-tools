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

from pharaoh.config.base import ConfigurationBase
from pharaoh.config.runtime import RuntimeStateConfig

logger = logging.getLogger('pharaoh.config.main')

class Configuration(ConfigurationBase):
    @property
    def runstate(self):
        return self.state['runstate']

    @runstate.setter
    def runstate(self, value):
        if isinstance(value, RuntimeStateConfig):
            value.conf = self
            self.state['runstate'] = value
        else:
            msg = "invalid runtime state"
            logger.critical(msg)
            raise TypeError(msg)
