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

logger = logging.getLogger('giza.content.extract.models')

from giza.core.inheritance import InheritableContentBase
from giza.content.steps.models import HeadingMixin

class ExtractData(HeadingMixin, InheritableContentBase):
    _default_level = 2

    @property
    def append(self):
        return self._get_file('append')

    @append.setter
    def append(self, value):
        self._set_file(value, 'append')

    @property
    def prepend(self):
        return self._get_file('prepend')

    @prepend.setter
    def prepend(self, value):
        self._set_file('prepend')

    @property
    def class(self):
        return self.state['class']

    @class.setter
    def class(self, value):
        self.state['class'] = value

    @property
    def target(self):
        return os.path.join(self.conf.system.content.extracts.output_dir, self.ref) + '.rst'

    ## The actual implementation for prepend/append
    def _get_file(self, kind):
        if kind in self.state:
            return self.state[kind]
        else:
            return False

    def _set_file(self, value, kind):
        paths = [ os.path.abspath(value),
                  os.path.join(self.conf.paths.projectroot, value),
                  os.path.join(self.conf.paths.projectroot,
                               self.conf.paths.branch_source, value),
                  os.path.join(self.conf.paths.projectroot,
                               self.conf.paths.branch_includes, value) ]

        for path in paths:
            if os.path.isfile(path):
                self.state[kind] = path
                return

        logger.error('cannot {0} to non existing file "{1}", skipping.'.format(kind, value))
