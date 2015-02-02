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

logger = logging.getLogger('giza.content.options.tasks')

from giza.tools.files import expand_tree, verbose_remove, safe_create_directory
from giza.content.options.inheritance import OptionDataCache
from giza.content.options.views import render_options
from giza.config.content import new_content_type
from giza.core.task import Task

def register_options(conf):
    conf.system.content.add(name='options', definition=new_content_type(name='option', task_generator=option_tasks, conf=conf))

def write_options(option, fn, conf):
    content = render_options(option, conf)
    content.write(fn)
    logger.info('wrote options file: ' + fn)

def option_tasks(conf):
    o = OptionDataCache(conf.system.content.options.sources, conf)
    o.create_output_dir()

    tasks = []
    for dep_fn, option in o.content_iter():
        output_fn = os.path.join(conf.system.content.options.fn_prefix,
                                 ''.join((option.directive, '-', option.program, '-', option.name, '.rst'))

        t = Task(job=write_options,
                 args=(option, output_fn, conf),
                 description='generating option file "{0}" from "{1}"'.format(output_fn, dep_fn),
                 target=output_fn,
                 dependency=[dep_fn])
        tasks.append(t)

    logger.info("added tasks for {0} option generation tasks".format(len(tasks)))
    return tasks

def option_clean(conf, app):
    register_options(conf)

    for fn in conf.system.options.sources:
        task = app.add('task')
        task.job = verbose_remove
        task.args = [fn]
        task.description = 'removing {0}'.format(fn)
