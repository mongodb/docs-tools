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

import os.path

from giza.inheritance import DataContentBase, DataCache
from giza.content.glossary.models import GlossaryData


class GlossaryFile(DataContentBase):
    content_class = GlossaryData

    def target(self, fn):
        # fn is the source file
        return os.path.join(self.conf.system.content.glossary.output_dir,
                            self.conf.system.content.glossary.get_basename(fn)) + '.rst'


class GlossaryDataCache(DataCache):
    content_class = GlossaryFile
    content_type = 'glossary'
