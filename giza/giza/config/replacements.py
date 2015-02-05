# 2014 MongoDB, Inc.
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

from libgiza.config import RecursiveConfigurationBase

logger = logging.getLogger('giza.config.sphinx_config')


class ReplacementData(RecursiveConfigurationBase):

    def ingest(self, input_obj):
        if isinstance(input_obj, list):
            if len(input_obj) == 1 and isinstance(input_obj[0], dict):
                input_obj = input_obj[0]
            else:
                try:
                    input_obj = dict((item['edition'], item) for item in input_obj)
                except KeyError:
                    logger.error("replacement specification is malformed. documents need editions")
                    return

        if self.conf.project.edition == self.conf.project.name:
            if self.conf.project.name in input_obj:
                self._update_tokens(input_obj[self.conf.project.name])
            else:
                if self._validate_tokens(input_obj) is True:
                    self._update_tokens(input_obj)

        if self.conf.project.edition in input_obj:
            self._update_tokens(input_obj[self.conf.project.edition])
        else:
            logger.error('current edition not defined for replacements, adding no replacements')

    def _validate_tokens(self, tokens):
        for value in tokens.items():
            if isinstance(value, dict):
                logger.error("replacement tokens cannot specify mappings")
                return False

        return True

    def _update_tokens(self, new_keys):
        if 'tokens' in new_keys:
            self.state.update(new_keys['tokens'])
        else:
            self.state.update(new_keys)

    def items(self):
        return self.state.items()

    def keys(self):
        return self.state.keys()

    def values(self):
        return self.state.values()

    def update(self, value):
        self._update_tokens(value)
