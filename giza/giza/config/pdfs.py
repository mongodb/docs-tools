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

logger = logging.getLogger('giza.config.helper')


class PdfConfig(ConfigurationBase):
    _option_registry = ['source', 'title', 'tag', 'author', 'class', 'edition']

    @property
    def output(self):
        return self.state['output']

    @output.setter
    def output(self, value):
        if value.endswith('.tex'):
            self.state['output'] = value
        else:
            raise TypeError

    @property
    def doc_class(self):
        return self.state['class']

    @doc_class.setter
    def doc_class(self, value):
        if value in ('manual', 'howto'):
            self.state['class'] = value
        else:
            raise TypeError
