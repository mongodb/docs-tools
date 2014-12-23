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
from giza.tools.strings import hyph_concat
from giza.content.options.inheritance import OptionDataCache
from giza.content.options.views import render_options
from giza.config.content import new_content_type

def register_options(conf):
    conf.system.content.add(name='options', definition=new_content_type(name='option', task_generator=option_tasks, conf=conf))

def write_options(option, fn, conf):
    content = render_options(option, conf)
    content.write(fn)
    logger.info('wrote options file: ' + fn)

def option_tasks(conf, app):
    register_options(conf)

    option_sources = conf.system.content.options.sources
    o = OptionDataCache(option_sources, conf)

    if len(option_sources) > 0 and not os.path.isdir(conf.system.content.options.output_dir):
        safe_create_directory(conf.system.content.options.output_dir)

    for dep_fn, option in o.content_iter():
        if option.program.startswith('_'):
            continue

        out_fn = hyph_concat(option.directive, option.program, option.name) + '.rst'
        output_fn = os.path.join(conf.system.content.options.fn_prefix, out_fn)

        t = app.add('task')
        t.target = output_fn
        t.dependency = [dep_fn]
        t.job = write_options
        t.args = (option, output_fn, conf)
        t.description = 'generating option file "{0}" from "{1}"'.format(output_fn, dep_fn)

def option_clean(conf, app):
    register_options(conf)

    for fn in conf.system.options.sources:
        task = app.add('task')
        task.job = verbose_remove
        task.args = [fn]
        task.description = 'removing {0}'.format(fn)
