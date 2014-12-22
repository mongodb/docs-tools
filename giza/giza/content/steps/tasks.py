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

logger = logging.getLogger('giza.content.steps.tasks')

from giza.tools.files import expand_tree, verbose_remove
from giza.content.steps.inheritance import StepDataCache
from giza.content.steps.views import render_steps

def write_steps(steps, fn, conf):
    content = render_steps(steps, conf)
    content.write(fn)
    logger.info('wrote steps to: '  + fn)

def get_step_fn_prefix(conf):
    return os.path.join(conf.paths.projectroot, conf.paths.branch_includes, 'steps')

def step_outputs(conf):
    include_dir = os.path.join(conf.paths.projectroot, conf.paths.branch_includes)
    fn_prefix = get_step_fn_prefix(conf)

    return [ fn for fn in
             expand_tree(include_dir, 'yaml')
             if fn.startswith(fn_prefix) ]

def step_tasks(conf, app):
    fn_prefix = get_step_fn_prefix(conf)
    step_sources = step_outputs(conf)
    s = StepDataCache(step_sources, conf)

    if len(step_sources) and not os.path.isdir(fn_prefix):
        os.makedirs(fn_prefix)

    for fn, stepf in s.file_iter():
        basename = fn[len(fn_prefix)+1:-5]

        out_fn = os.path.join(conf.paths.projectroot,
                              conf.paths.branch_includes,
                              'steps', basename) + '.rst'

        t = app.add('task')
        t.target = out_fn
        t.dependency = fn
        t.job = write_steps
        t.args = (stepf, out_fn, conf)
        t.description = 'generate an stepfile for ' + fn

def step_clean(conf, app):
    for fn in step_outputs(conf):
        task = app.add('task')
        task.job = verbose_remove
        task.args = [fn]
        task.description = 'removing {0}'.format(fn)
