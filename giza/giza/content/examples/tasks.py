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

from giza.tools.files import verbose_remove
from giza.config.content import new_content_type
from giza.content.examples.inheritance import ExampleDataCache
from giza.content.examples.views import full_example
from libgiza.task import Task

logger = logging.getLogger('giza.content.examples')


def register_examples(conf):
    content_dfn = new_content_type(name='examples',
                                   task_generator=example_tasks,
                                   conf=conf)

    conf.system.content.add(name='examples', definition=content_dfn)


def write_full_example(collection, examples, fn):
    content = full_example(collection, examples)
    content.write(fn)


def example_tasks(conf):
    d = ExampleDataCache(conf.system.content.examples.sources, conf)
    d.create_output_dir()

    tasks = []
    for fn, exmpf in d.file_iter():
        out_fn = os.path.join(conf.system.content.examples.output_dir,
                              conf.system.content.examples.get_basename(fn)) + '.rst'

        t = Task(job=write_full_example,
                 args=(exmpf.collection, exmpf.examples, out_fn),
                 description='generate an example for ' + fn,
                 target=out_fn,
                 dependency=fn)
        tasks.append(t)

    logger.info("added tasks for {0} example generation tasks".format(len(tasks)))
    return tasks


def example_clean(conf, app):
    register_examples(conf)

    for fn in conf.system.content.examples.sources:
        out_fn = os.path.join(conf.system.content.examples.output_dir,
                              conf.system.content.examples.get_basename(fn)) + '.rst'

        t = app.add('task')
        t.target = True
        t.dependency = out_fn
        t.job = verbose_remove
        t.args = [out_fn]
