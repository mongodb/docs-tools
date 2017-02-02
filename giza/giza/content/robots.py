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

"""
Generates a ``robot.txt`` file in the output directory. Use to exclude content
from search engines that respect ``robots.txt``. Robots definitions resemble the
following: ::

   {
     "file": "/<path>",
     "branches": [
       <string,>
       # ..
       <string>
     ]
   }

You can specify "``{{published}}``" as a string in the branches array, to
exclude a path from all published branches, current and future.
"""

import os
import logging

import giza.libgiza.task
import giza.content.helper

logger = logging.getLogger('giza.content.robots')


def robots_txt_builder(fn, conf, override=False):
    if override is False:
        if conf.git.branches.current != 'master':
            logger.info('cowardly refusing to regenerate robots.txt on non-master branch.')
            return False
    else:
        logger.info('regenerating robots.txt on non-master branch with override.')

    if 'robots' not in conf.system.files.data:
        logger.warning('no robots directives configured. not generating robots.txt')
        return

    robots_txt_dir = os.path.dirname(fn)
    if not os.path.exists(robots_txt_dir):
        os.makedirs(robots_txt_dir)

    counter = 0
    with open(fn, 'w') as f:
        f.write('User-agent: *')
        f.write('\n')
        for record in conf.system.files.data.robots:
            if giza.content.helper.edition_check(record, conf) is False:
                counter += 1
                continue

            page = record['file']
            if 'branches' not in record:
                f.write('Disallow: {0}'.format(page))
                f.write('\n')
            else:
                for branch in record['branches']:
                    if branch == '{{published}}':
                        for pbranch in conf.git.branches.published:
                            f.write('Disallow: /{0}{1}'.format(pbranch, page))
                            f.write('\n')
                    else:
                        f.write('Disallow: /{0}{1}'.format(branch, page))
                        f.write('\n')

    if counter > 0 and counter == len(conf.system.files.data.robots):
        try:
            os.remove(fn)
            logger.debug('removed empty robots.txt file')
        except OSError:
            pass
    else:
        logger.info('regenerated {0} file.'.format(fn))


def robots_txt_tasks(conf):
    tasks = []

    if 'robots' in conf.system.files.data and len(conf.system.files.data.robots) > 0:
        dep_path = None
        for k in conf.system.files.paths:
            if k.startswith('robots'):
                dep_path = os.path.join(conf.paths.projectroot, conf.paths.builddata, k)
                break

        robots_fn = os.path.join(conf.paths.projectroot, conf.paths.public_site_output,
                                 'robots.txt')

        tasks.append(giza.libgiza.task.Task(job=robots_txt_builder,
                                            args=(robots_fn, conf),
                                            target=robots_fn,
                                            dependency=dep_path,
                                            description="building robots.txt file"))

    return tasks
