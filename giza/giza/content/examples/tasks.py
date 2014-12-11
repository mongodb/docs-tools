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

"""
Glues the reading and processing (:mod:`giza.content.examples.inheritance`) of
the example data (:mod:`giza.content.examples.models`) to the generation of the
output format (:mod:`giza.content.examples.views`).
"""

import logging
import os

logger = logging.getLogger('giza.content.examples')

from giza.tools.files import expand_tree, safe_create_directory, verbose_remove
from giza.content.examples.inheritance import ExampleDataCache
from giza.content.examples.views import full_example

def write_full_example(collection, examples, fn):
    content = full_example(collection, examples)
    content.write(fn)

def example_tasks(conf, app):
    # In the beginning of this operation, which executes in the main thread, we
    # read all files in "source/includes/" and sub-directories hat start with
    # "example-*"

    include_dir = os.path.join(conf.paths.projectroot, conf.paths.includes)
    fn_prefix = os.path.join(include_dir, 'example')

    example_sources = [ fn for fn in
                        expand_tree(include_dir, 'yaml')
                        if fn.startswith(fn_prefix) ]

    # process the corpus of example data.
    d = ExampleDataCache(example_sources, conf)

    if len(d) > 0:
        safe_create_directory(fn_prefix)

    for fn, exmpf in d.file_iter():
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

        t = app.add('task')
        t.target = True
        t.dependency = out_fn
        t.job = verbose_remove
        t.args = [out_fn]
