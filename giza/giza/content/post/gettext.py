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

import os.path
import logging

logger = logging.getLogger('giza.content.post.gettext')

from giza.tools.files import expand_tree, copy_if_needed
from giza.config.sphinx_config import resolve_builder_path

#################### Gettext Processing ####################

def gettext_tasks(conf, app):
    locale_dirs = os.path.join(conf.paths.projectroot,
                               conf.paths.locale, 'pot')

    builder_name = resolve_builder_path('gettext', conf.project.edition, None, conf)

    branch_output = os.path.join(conf.paths.projectroot,
                                 conf.paths.branch_output,
                                 builder_name)

    path_offset = len(branch_output) + 1

    for fn in expand_tree(branch_output, None):
        task = app.add('task')
        task.target = fn
        task.job = copy_if_needed
        task.args = [ fn, os.path.join(locale_dirs, fn[path_offset:]), None]
        task.description = "migrating po file {0} if needed".format(fn)
