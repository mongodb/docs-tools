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

from giza.config.base import ConfigurationBase

class AssetsConfig(ConfigurationBase):
    @property
    def path(self):
        return self.state['path']

    @path.setter
    def path(self, value):
        self.state['path'] = value

    @property
    def branch(self):
        return self.state['branch']

    @branch.setter
    def branch(self, value):
        self.state['branch'] = value

    @property
    def repository(self):
        return self.state['repository']

    @repository.setter
    def repository(self, value):
        self.state['repository'] = value
