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

from giza.inheritance import DataContentBase, DataCache
from giza.content.steps.models import StepData

logger = logging.getLogger('giza.content.steps.inheritance')


class StepFile(DataContentBase):
    content_class = StepData

    def add(self, doc):
        content = super(StepFile, self).add(doc)

        obj = self.content[content.ref]

        if 'number' not in obj:
            if len(self.content) == 1:
                obj.number = 1
            else:
                obj.number = self.fetch(self.ordering[-1]).number + 1

        return obj

    def target(self, fn):
        # fn is the source file
        return os.path.join(self.conf.system.content.steps.output_dir,
                            self.conf.system.content.steps.get_basename(fn)) + '.rst'


class StepDataCache(DataCache):
    content_class = StepFile
    content_type = 'steps'
