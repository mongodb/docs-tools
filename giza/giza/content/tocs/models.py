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

logger = logging.getLogger('giza.content.tocs.models')

if sys.version_info >= (3, 0):
    basestring = str


class TocData(InheritableContentBase):
    _option_registry = ['edition', 'name', 'description']

    @property
    def file(self):
        return self.state['file']

    @file.setter
    def file(self, value):
        if not isinstance(value, basestring):
            logger.error("filenames must be strings: " + str(value))
        elif not value.startswith("/"):
            logger.error("'{0}' is not a valid file specification".format(value))
            raise TypeError
        elif value.endswith(".rst") or value.endswith(".txt"):
            logger.error("file specifications cannot end with extensions: " + value)
            raise TypeError
        else:
            self.state['file'] = value

    @property
    def ref(self):
        if 'ref' not in self.state:
            self.ref = self.file

        return self.state['ref']

    @ref.setter
    def ref(self, value):
        self.state['ref'] = value

    @property
    def level(self):
        if 'level' not in self.state:
            return 1
        else:
            return self.state['level']

    @level.setter
    def level(self, value):
        if isinstance(value, int):
            self.state['level'] = value
        else:
            self.state['level'] = int(value)

    @property
    def text_only(self):
        if 'text_only' not in self.state:
            return False
        else:
            return self.state['text_only']

    @text_only.setter
    def text_only(self, value):
        if isinstance(value, bool):
            self.state['text_only'] = value
        else:
            self.state['text_only'] = bool(value)

    @property
    def is_spec(self):
        if self.source is None:
            return False
        else:
            return True
