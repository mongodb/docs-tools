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
import shutil

from giza.libgiza.task import Task

from giza.content.steps.inheritance import StepDataCache
from giza.content.steps.views import render_steps
from giza.config.content import new_content_type

logger = logging.getLogger('giza.content.steps.tasks')


def register_steps(conf):
    content_dfn = new_content_type(name='steps',
                                   task_generator=step_tasks,
                                   conf=conf)

    conf.system.content.add(name='steps', definition=content_dfn)


def write_steps(steps, fn, conf):
    content = render_steps(steps, conf)
    content.write(fn)
    logger.debug('wrote steps to: ' + fn)


def step_tasks(conf):
    s = StepDataCache(conf.system.content.steps.sources, conf)
    s.create_output_dir()

    tasks = []
    for fn, stepf in s.file_iter():
        t = Task(job=write_steps,
                 args=(stepf, stepf.target(fn), conf),
                 description='generate a stepfile for ' + fn,
                 target=stepf.target(fn),
                 dependency=fn)
        tasks.append(t)

    logger.debug('added tasks for {0} step generation tasks'.format(len(tasks)))
    return tasks


def step_clean(conf):
    return [Task(job=shutil.rmtree,
                 args=[conf.system.content.steps.output_dir],
                 target=True,
                 dependency=[conf.system.content.steps.output_dir],
                 description='removing {0}'.format(conf.system.content.steps.output_dir))]
