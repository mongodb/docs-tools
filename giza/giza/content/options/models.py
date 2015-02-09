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
import sys

from giza.inheritance import InheritableContentBase, InheritanceReference

logger = logging.getLogger('giza.content.options.models')

if sys.version_info >= (3, 0):
    basestring = str


class OptionData(InheritableContentBase):
    _option_registry = ['pre', 'post', 'final', 'ref', 'content', 'edition',
                        'description', 'name', 'args', 'aliases', 'default', 'type']

    @property
    def source(self):
        if 'source' in self.state:
            return self.state['source']
        else:
            return None

    @source.setter
    def source(self, value):
        value['ref'] = (value['program'], value['name'])
        del value['program']
        del value['name']

        self.state['source'] = InheritanceReference(value, self.conf)

    inherit = source

    @property
    def program(self):
        return self.state['program']

    @program.setter
    def program(self, value):
        if isinstance(value, basestring):
            self.state['program'] = value
            self.state['ref'] = value
        else:
            raise TypeError

    @property
    def optional(self):
        if 'optional' in self.state:
            return self.state['optional']
        else:
            return True

    @optional.setter
    def optional(self, value):
        if isinstance(value, bool):
            self.state['optional'] = value
        else:
            raise TypeError

    @property
    def directive(self):
        if 'directive' in self.state:
            return self.state['directive']
        else:
            return 'object'

    @directive.setter
    def directive(self, value):
        if (value in ('option', 'data', 'setting',
                      'method', 'function', 'class') or
                value.endswith('setting')):
            self.state['directive'] = value
        else:
            raise TypeError
