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

from giza.inheritance import DataContentBase, DataCache
from giza.content.apiargs.models import ApiArgData

logger = logging.getLogger('giza.content.inheritance.apiargs')


class ApiArgFile(DataContentBase):
    content_class = ApiArgData

    def field_type(self):
        name = set()

        for content in self.content.values():
            name.add(content.arg_name_rendered)

        if len(name) > 1:
            logger.warning('too many field types returning one at random.')

        return name.pop()

    def has_type(self):
        for content in self.content.values():
            if 'type' in content:
                return True

        return False


class ApiArgDataCache(DataCache):
    content_class = ApiArgFile
    content_type = 'apiargs'
