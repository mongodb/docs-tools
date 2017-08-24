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
import time

logger = logging.getLogger('giza.tools.timing')


class Timer():

    def __init__(self, name=None):
        if name is None:
            self.name = 'task'
        else:
            self.name = name

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args):
        logger.debug('time elapsed for "{0}" was: {1}'.format(
            self.name, str(time.time() - self.start)))
