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

from giza.content.release.inheritance import ReleaseDataCache
from giza.content.release.views import render_releases
from giza.config.content import new_content_type
from giza.libgiza.task import Task

logger = logging.getLogger('giza.content.release.tasks')


def register_releases(conf):
    content_dfn = new_content_type(name='release',
                                   task_generator=release_tasks,
                                   conf=conf)

    conf.system.content.add(name='releases', definition=content_dfn)


def write_release_file(release, fn, conf):
    content = render_releases(release, conf)
    content.write(fn)
    logger.debug('wrote release content: ' + fn)


def release_tasks(conf):
    rel = ReleaseDataCache(conf.system.content.releases.sources, conf)
    rel.create_output_dir()

    tasks = []
    for dep_fn, release in rel.content_iter():
        t = Task(job=write_release_file,
                 args=(release, release.target, conf),
                 description='generating release spec file: ' + release.target,
                 target=release.target,
                 dependency=dep_fn)
        tasks.append(t)

    logger.debug('added tasks for {0} release generation tasks'.format(len(tasks)))
    return tasks


def release_clean(conf):
    return [Task(job=shutil.rmtree,
                 args=[conf.system.content.releases.output_dir],
                 target=True,
                 dependency=[conf.system.content.releases.output_dir],
                 description='removing {0}'.format(conf.system.content.releases.output_dir))]
