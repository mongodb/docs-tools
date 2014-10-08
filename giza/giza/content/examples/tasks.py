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
import os

logger = logging.getLogger('giza.content.examples')

from giza.tools.files import expand_tree
from giza.content.examples.inheritance import ExampleDataCache
from giza.content.examples.views import full_example

def write_full_example(collection, examples, fn):
    content = full_example(collection, examples)
    content.write(fn)

def example_tasks(conf, app):
    include_dir = os.path.join(conf.paths.projectroot, conf.paths.includes)
    fn_prefix = os.path.join(include_dir, 'example')

    example_sources = [ fn for fn in
                        expand_tree(include_dir, 'yaml')
                        if fn.startswith(fn_prefix) ]

    d = ExampleDataCache(example_sources, conf)

    if not os.path.isdir(fn_prefix):
        os.makedirs(fn_prefix)

    for fn in d.cache.keys():
        exmpf = d.cache[fn]
        basename = fn[len(fn_prefix)+1:-5]

        out_fn = os.path.join(conf.paths.projectroot,
                              conf.paths.branch_source,
                              'includes', 'examples', basename) + '.rst'

        t = app.add('task')
        t.target = out_fn
        t.dependency = fn
        t.job = write_full_example
        t.args = (exmpf.collection, exmpf.examples, out_fn)
        t.description = 'generate an example for ' + basename

    logger.debug('added all tasks for example generation')

def example_clean(conf, app):
    fn_prefix = os.path.join(include_dir, 'example')

    example_sources = [ fn for fn in
                        expand_tree(include_dir, 'yaml')
                        if fn.startswith(fn_prefix) ]

    for fn in example_sources:
        basename = fn[len(fn_prefix)+1:-5]

        out_fn = os.path.join(conf.paths.projectroot,
                              conf.paths.branch_source,
                              'includes', 'examples', basename) + '.rst'
