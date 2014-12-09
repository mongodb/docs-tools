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

from giza.tools.files import expand_tree, verbose_remove
from giza.tools.strings import hyph_concat
from giza.content.options.inheritance import OptionDataCache
from giza.content.options.views import render_options

def get_option_fn_prefix(conf):
    return os.path.join(conf.paths.projectroot, conf.paths.includes, 'option')

def option_outputs(conf):
    include_dir = os.path.join(conf.paths.projectroot, conf.paths.includes)

    fn_prefix = get_option_fn_prefix(conf)

    return [ fn for fn in
             expand_tree(include_dir, 'yaml')
             if fn.startswith(fn_prefix) ]

def write_options(option, fn, conf):
    content = render_options(option, conf)
    content.write(fn)

def option_tasks(conf, app):
    fn_prefix = get_option_fn_prefix(conf)
    option_sources = option_outputs(conf)
    o = OptionDataCache(option_sources, conf)

    if len(option_sources) and not os.path.isdir(fn_prefix):
        os.makedirs(fn_prefix)

    for dep_fn, option in o.options:
        if option.program.startswith('_'):
            continue

        out_fn = hyph_concat(option.directive, option.program, option.name) + '.rst'
        output_fn = os.path.join(fn_prefix, out_fn)

        t = app.add('task')
        t.target = out_fn
        t.dependency = dep_fn
        t.job = write_options
        t.args = (option, out_fn, conf)
        t.description = 'generating option file "{0}" from "{1}"'.format(out_fn, dep_fn)

def option_clean(conf, app):
    for fn in option_outputs(conf):
        task = app.add('task')
        task.job = verbose_remove
        task.args = [fn]
        task.description = 'removing {0}'.format(fn)
