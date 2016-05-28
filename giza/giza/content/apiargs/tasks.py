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

import os
import logging

from libgiza.task import Task

from giza.content.apiargs.inheritance import ApiArgDataCache
from giza.content.apiargs.views import render_apiargs
from giza.config.content import new_content_type

logger = logging.getLogger('giza.content.apiargs.tasks')


def register_apiargs(conf):
    content_def = new_content_type(name='apiargs',
                                   task_generator=apiarg_tasks,
                                   conf=conf)

    conf.system.content.add(name='apiargs', definition=content_def)


def write_apiargs(apiargs, fn):
    content = render_apiargs(apiargs)
    content.write(fn)
    logger.info('wrote apiarg table to: ' + fn)


def apiarg_tasks(conf):
    a = ApiArgDataCache(conf.system.content.apiargs.sources, conf)
    a.create_output_dir()

    tasks = []
    for dep_fn, apiargs in a.file_iter():
        basename = conf.system.content.steps.get_basename(dep_fn)[2:]
        out_fn = os.path.join(conf.system.content.apiargs.output_dir, basename) + '.rst'

        t = Task(job=write_apiargs,
                 args=(apiargs, out_fn),
                 target=out_fn,
                 dependency=dep_fn,
                 description="write apiarg table for: " + dep_fn)
        tasks.append(t)

    logger.info('added tasks for {0} apiarg table generation tasks'.format(len(tasks)))

    return tasks
