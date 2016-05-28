# Copyright 2015 MongoDB, Inc.
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

from giza.inheritance import InheritableContentBase

logger = logging.getLogger('giza.content.glossary.models')

if sys.version_info >= (3, 0):
    basestring = str


class GlossaryData(InheritableContentBase):
    @property
    def term(self):
        return self.state['term']

    @term.setter
    def term(self, value):
        if isinstance(value, basestring):
            self.state['term'] = value
        else:
            raise TypeError

    @property
    def definition(self):
        return self.state['definition']

    @definition.setter
    def definition(self, value):
        if isinstance(value, basestring):
            self.state['definition'] = value
        else:
            raise TypeError
