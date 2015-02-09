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
from giza.content.tocs.models import TocData

logger = logging.getLogger('giza.content.tocs.inheritance')


class TocFile(DataContentBase):
    content_class = TocData

    def ordered_items(self):
        return [
            self.fetch(ref)
            for ref in self.ordering
        ]

    def is_spec(self):
        for content_item in self.content.values():
            if content_item.source is None:
                continue
            else:
                return True

        return False

    def spec_deps(self):
        deps = []
        for content_item in self.content.values():
            if content_item.source is None:
                continue
            else:
                deps.append(content_item.source.file)

        return deps


class TocDataCache(DataCache):
    content_class = TocFile
    content_type = 'toc'
