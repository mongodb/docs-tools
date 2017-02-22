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

from giza.libgiza.config import ConfigurationBase


class AssetsConfig(ConfigurationBase):
    _option_registry = ['path', 'branch', 'repository', 'commit']

    @property
    def generate(self):
        return self.state['generate']

    @generate.setter
    def generate(self, value):
        if isinstance(value, list):
            self.state['generate'] = value
        else:
            raise TypeError
