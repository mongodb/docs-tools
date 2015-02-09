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
import os.path
import sys

from giza.inheritance import InheritableContentBase
from giza.content.steps.models import HeadingMixin

logger = logging.getLogger('giza.content.extract.models')

if sys.version_info >= (3, 0):
    basestring = str


class ExtractData(HeadingMixin, InheritableContentBase):
    _default_level = 2

    @property
    def only(self):
        return self.state['only']

    @only.setter
    def only(self, value):
        if isinstance(value, basestring):
            self.state['only'] = value
        else:
            raise TypeError

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
        self._set_file(value, 'prepend')

    @property
    def style(self):
        return self.state['style']

    @style.setter
    def style(self, value):
        self.state['style'] = value

    @property
    def target(self):
        return os.path.join(self.conf.system.content.extracts.output_dir, self.ref) + '.rst'

    @property
    def target_project_path(self):
        offset = len(os.path.join(self.conf.paths.projectroot, self.conf.paths.branch_source))

        return self.target[offset:]

    # The actual implementation for prepend/append
    def _get_file(self, kind):
        if kind in self.state:
            return self.state[kind]
        else:
            return []

    def _set_file(self, value, kind):
        if not isinstance(value, list):
            value = [value]

        paths = []
        for fn in value:
            if fn.startswith(os.path.sep):
                fn = fn[1:]
            for path in [os.path.join(self.conf.paths.projectroot,
                                      self.conf.paths.branch_source, fn),
                         os.path.join(self.conf.paths.projectroot,
                                      self.conf.paths.branch_includes, fn),
                         os.path.join(self.conf.paths.projectroot, fn),
                         os.path.abspath(fn)]:
                if os.path.isfile(path):
                    paths.append(path)
                    break

        self.state[kind] = paths
        if len(value) > 0 and len(paths) < 0:
            logger.error('cannot {0} to non existing file "{1}", skipping.'.format(kind, value))
