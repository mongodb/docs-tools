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

logger = logging.getLogger('giza.content.release.tasks')

from giza.tools.files import expand_tree, verbose_remove
from giza.content.release.inheritance import ReleaseDataCache
from giza.content.release.views import render_releases

def get_release_fn_prefix(conf):
    return os.path.join(conf.paths.projectroot, conf.paths.branch_includes, 'release')

def release_outputs(conf):
    include_dir = os.path.join(conf.paths.projectroot, conf.paths.branch_includes)

    fn_prefix = get_release_fn_prefix(conf)

    return [ fn for fn in
             expand_tree(include_dir, 'yaml')
             if fn.startswith(fn_prefix) ]

def write_release_file(release, fn, conf):
    content = render_releases(release, conf)
    content.write(fn)

def release_tasks(conf, app):
    fn_prefix = get_release_fn_prefix(conf)
    release_sources = release_outputs(conf)
    rel = ReleaseDataCache(release_sources, conf)

    if len(release_sources) and not os.path.isdir(fn_prefix):
        os.makedirs(fn_prefix)

    for dep_fn, release in rel.content_iter():
        if release.ref.startswith('_'):
            continue

        out_fn = os.path.join(fn_prefix, release.ref) + '.rst'

        t = app.add('task')
        t.job = write_release_file
        t.target = out_fn
        t.dependency = dep_fn
        t.args = (release, out_fn, conf)
        t.description = 'generating release spec file: ' + out_fn

def release_clean(conf, app):
    for fn in release_outputs(conf):
        task = app.add('task')
        task.job = verbose_remove
        task.args = [fn]
        task.description = 'removing {0}'.format(fn)
