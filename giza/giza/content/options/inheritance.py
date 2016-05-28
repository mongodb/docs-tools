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

from giza.inheritance import DataContentBase, DataCache
from giza.content.options.models import OptionData

logger = logging.getLogger('giza.content.options.inheritance')


class OptionFile(DataContentBase):
    content_class = OptionData

    def add(self, doc):
        content = self.content_class(doc, self.conf)

        ref = (content.program, content.name)

        if not content.is_resolved():
            content.resolve(self.data)

        self.content[ref] = content

        return content


class OptionDataCache(DataCache):
    content_class = OptionFile
    content_type = 'options'
