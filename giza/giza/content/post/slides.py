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
For slides builds, build a tarball and migrate source to the output
directory. Modeled on the :mod:`giza.content.post.json_output` and
:mod:`giza.content.post.html` post-processing operation.
"""

import os
import logging
import subprocess

import libgiza.task
from giza.content.post.archives import slides_tarball, get_tarball_name

logger = logging.getLogger('giza.content.post.slides')


def slides_output(conf):
    cmd = 'rsync --recursive --times --delete {src} {dst}'

    dst = os.path.join(conf.paths.public_site_output, 'slides')

    if not os.path.exists(dst):
        logger.debug('created directories for {0}'.format(dst))
        os.makedirs(dst)

    builder = 'slides'

    if 'edition' in conf.project and conf.project.edition != conf.project.name:
        builder += '-' + conf.project.edition

    cmd_str = cmd.format(src=os.path.join(conf.paths.branch_output, builder) + '/',
                         dst=dst)

    with open(os.devnull, 'w') as f:
        try:
            subprocess.check_call(args=cmd_str.split(),
                                  stdout=f,
                                  stderr=f)
            logger.info('deployed slides local staging.')
        except subprocess.CalledProcessError:
            logger.error('issue deploying slides to local staging')


def slide_tasks(sconf, conf):
    return [libgiza.task.Task(job=slides_tarball,
                              target=[get_tarball_name('slides', conf),
                                      get_tarball_name('link-slides', conf)],
                              args=(sconf.name, sconf.build_output, conf),
                              description="creating tarball for slides"),
            libgiza.task.Task(job=slides_output,
                              args=[conf],
                              description='migrating slide output to production')]
