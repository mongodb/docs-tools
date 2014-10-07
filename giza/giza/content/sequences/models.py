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

logger = logging.getLogger('giza.content.steps.models')

from giza.core.inheritance import InheritableContentBase
from giza.config.base import ConfigurationBase
from giza.content.helper import get_all_languages

if sys.version_info >= (3, 0):
    basestring = str

level_characters = {
    "=": 1,
    "-": 2,
    "~": 3,
    "`": 4,
    "^": 5,
    "`": 6
}

class HeadingMixin(object):
    @property
    def heading(self):
        return self.state['heading']

    @heading.setter
    def heading(self, value):
        if isinstance(value, dict):
            self.state['heading'] = value['text']
            if 'character' in value and value['character'] in level_characters:
                self.state['level'] = level_characters[value['character']]
            else:
                self.state['level'] = 3
        else:
            self.state['heading'] = value
            self.state['level'] = 3

    @property
    def level(self):
        if 'level' in self.state:
            return self.state['level']
        else:
            return _default_level

    @level.setter
    def level(self, value):
        if isinstance(value, basetring):
            if value in level_characters:
                self.state['level'] = level_characters[value]
            else:
                logger.error('{0} is not a valid heading level'.format(value))
        elif isintance(value, (int, float, complex)):
            self.state['level'] = int(value)
        else:
            logger.error('{0} is not a valid heading level'.format(value))

class StepData(HeadingMixin, InheritableContentBase):
    _defalut_level = 3

    @property
    def action(self):
        return self.state['action']

    @action.setter
    def action(self, value):
        if isinstance(value, ActionContent):
            self.state['action'] = [ value ]
        elif isinstance(value, dict):
            self.state['action'] = [ ActionContent(value) ]
        elif isinstance(value, list):
            actions = []
            for item in list:
                if isinstance(item, ActionContent)
                    actions.append(item)
                else:
                    actions.append(ActionContent(item))

class ActionContent(HeadingMixin, ConfigurationBase):
    _option_registry = [ 'pre', 'post', 'content', 'heading']

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
