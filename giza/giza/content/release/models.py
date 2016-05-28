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

from giza.inheritance import InheritableContentBase
from giza.content.steps.models import HeadingMixin
from giza.content.helper import get_all_languages

logger = logging.getLogger('giza.content.models')


class ReleaseData(HeadingMixin, InheritableContentBase):
    _option_registry = ['ref', 'description', 'pre', 'post', 'content']

    @property
    def target(self):
        return os.path.join(self.conf.system.content.releases.fn_prefix, self.ref) + '.rst'

    @property
    def code(self):
        return self.state['code']

    @code.setter
    def code(self, value):
        if isinstance(value, list):
            self.state['code'] = value
        else:
            self.state['code'] = value.split('\n')

    @property
    def language(self):
        return self.state['language']

    @language.setter
    def language(self, value):
        if value in get_all_languages():
            self.state['language'] = value
        else:
            m = '{0} is not a supported language'.format(value)
            logger.error(m)
            TypeError(m)
