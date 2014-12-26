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

from giza.tools.files import expand_tree, verbose_remove, safe_create_directory
from giza.content.release.inheritance import ReleaseDataCache
from giza.content.release.views import render_releases
from giza.config.content import new_content_type

def register_releases(conf):
    conf.system.content.add(name='releases', definition=new_content_type(name='release', task_generator=release_tasks, conf=conf))

def write_release_file(release, fn, conf):
    content = render_releases(release, conf)
    content.write(fn)
    logger.info('wrote release content: ' + fn)

def release_tasks(conf, app):
    register_releases(conf)
    release_sources = conf.system.content.releases.sources

    rel = ReleaseDataCache(release_sources, conf)

    if len(release_sources) > 0 and not os.path.isdir(conf.system.content.releases.output_dir):
        safe_create_directory(conf.system.content.releases.output_dir)

    for dep_fn, release in rel.content_iter():
        t = app.add('task')
        t.job = write_release_file
        t.target = release.target
        t.dependency = dep_fn
        t.args = (release, release.target, conf)
        t.description = 'generating release spec file: ' + release.target

def release_clean(conf, app):
    register_releases(conf)

    rel = ReleaseDataCache(conf.system.content.releases.sources, conf)

    for dep, release in rel.content_iter():
        task = app.add('task')
        task.target = True
        task.dependency = fn
        task.job = verbose_remove
        task.args = [release.target]
        task.description = 'removing {0}'.format(fn)
