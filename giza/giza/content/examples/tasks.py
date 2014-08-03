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

logger = logging.getLogger('giza.content.examples')

from giza.files import expand_tree
from giza.content.examples.inheritance import ExampleDataCache

def example_tasks(conf):
    include_dir = os.path.join(conf.paths.projectroot, conf.paths.includes)

    example_sources = [ fn for fn in
                        expand_tree(include_dir, 'yaml')
                        if fn.startswith(os.path.join(include_dir, 'example')) ]

    d = ExampleDataCache(example_sources, conf)


    for fn in d.cache.keys():
        exmpf = d.cache[fn]

        print('---\n' + fn + '\n')
        print('Collection:\n\n' + str(exmpf.collection) + '\n\n')
        print('Examples:\n\n ' + str(exmpf.get_content_only()))
