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

import os
import logging
import shutil

logger = logging.getLogger('giza.content.steps.tasks')

from giza.tools.files import expand_tree, safe_create_directory
from giza.content.steps.inheritance import StepDataCache
from giza.content.steps.views import render_steps
from giza.config.content import new_content_type
from giza.core.task import Task

def register_steps(conf):
    conf.system.content.add(name='steps', definition=new_content_type(name='steps', task_generator=step_tasks, conf=conf))

def write_steps(steps, fn, conf):
    content = render_steps(steps, conf)
    content.write(fn)
    logger.info('wrote steps to: '  + fn)

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

    logger.info("added tasks for {0} step generation tasks".format(len(tasks)))
    return tasks

def step_clean(conf, app):
    task = app.add('task')
    task.target = True
    task.dependnecy = fn
    task.job = shutil.rmtree
    task.args = [conf.system.content.steps.output_dir]
    task.description = 'removing {0}'.format(conf.system.content.steps.output_dir)
