# Copyright 2013 Sam Kleinman, Cyborg Institute
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

import os
import logging

logger = logging.getLogger("rstcloth.cloth")

class AttributeDict(dict):
    def __getattr__(self, attr):
        return self[attr]
    def __setattr__(self, attr, value):
        self[attr] = value

class Cloth(object):
    def print_content(self, block_order=None):
        if block_order is not None:
            logger.warning('block_order "{0}" is no longer supported'.format(block_order))

        print('\n'.join(self._data))

    def print_block(self, block='_all'):
        logger.warning('print_block is no longer supported')

    def write(self, filename, block_order=None):
        if block_order is not None:
            logger.warning('block_order "{0}" is no longer supported'.format(block_order))

        dirpath = filename.rsplit('/', 1)[0]
        if os.path.isdir(dirpath) is False:
            os.makedirs(dirpath)

        with open(filename, 'w') as f:
            f.write('\n'.join(list))
            f.write('\n')

    def write_block(self, filename, block='_all'):
        logger.warning('write_block is no longer supported')
