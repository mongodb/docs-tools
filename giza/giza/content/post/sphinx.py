# Copyright 2015 MongoDB, Inc.
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
import os.path

from giza.libgiza.task import Task

from giza.content.post.json_output import json_output_tasks
from giza.content.post.singlehtml import finalize_single_html_tasks
from giza.content.post.archives import man_tarball, html_tarball, get_tarball_name
from giza.content.post.manpages import manpage_url_tasks
from giza.content.post.gettext import gettext_tasks
from giza.content.post.slides import slide_tasks
from giza.content.post.latex import pdf_tasks
from giza.content.post.sites import (finalize_epub_build,
                                     finalize_dirhtml_build, error_pages)

logger = logging.getLogger('giza.content.post.sphinx')


def printer(string):
    logger.info(string)


def finalize_sphinx_build(sconf, conf):
    target = sconf.builder

    tasks = []
    if target == 'html' and not conf.runstate.fast:
        t = Task(job=html_tarball,
                 args=(sconf.name, sconf.build_output, conf),
                 target=[get_tarball_name('html', conf),
                         get_tarball_name('link-html', conf)],
                 dependency=None,
                 description="creating tarball for html archive")
        tasks.append(t)
    elif target == 'dirhtml' and not conf.runstate.fast:
        # We're experiencing some cases were giza seemingly randomly doesn't migrate.
        # Log this to help us figure out what's going on.
        logger.info('Going to migrate {} to {}'.format(
            sconf.fq_build_output,
            os.path.join(conf.paths.projectroot, conf.paths.public_site_output)))

        for job in (finalize_dirhtml_build, error_pages):
            t = Task(job=job,
                     args=(sconf, conf),
                     target=os.path.join(conf.paths.projectroot, conf.paths.public_site_output),
                     dependency=None)
            tasks.append(t)
    elif target == 'epub':
        t = Task(job=finalize_epub_build,
                 args=(target, conf),
                 description='finalizing epub build',
                 dependency=None,
                 target=True)
        tasks.append(t)
    elif target == 'man':
        t = Task(job=man_tarball,
                 args=(sconf.name, sconf.build_output, conf),
                 target=[get_tarball_name('man', conf),
                         get_tarball_name('link-man', conf)],
                 dependency=None,
                 description="creating tarball for manpages")

        tasks.extend(manpage_url_tasks(target, conf))
        tasks.append(('final', t))
    elif target == 'slides' and not conf.runstate.fast:
        tasks.extend(slide_tasks(sconf, conf))
    elif target == 'json':
        json_tasks, transfer_op = json_output_tasks(conf)
        tasks.extend(json_tasks)
        tasks.append(('final', transfer_op))  # this is less than ideal
    elif target == 'singlehtml':
        tasks.extend(finalize_single_html_tasks(target, conf))
    elif target == 'latex':
        tasks.extend(pdf_tasks(sconf, conf))
    elif target == 'gettext':
        tasks.extend(gettext_tasks(conf))
    elif target == 'linkcheck':
        msg_str = '{0}: See {1}/{0}/output.txt for output.'
        t = Task(job=printer,
                 args=[msg_str.format(target, conf.paths.branch_output)],
                 target=os.path.join(conf.paths.projectroot,
                                     conf.paths.branch_output, target, 'output.txt'),
                 dependency=None)
        tasks.append(t)

    logger.debug('adding {0} finalizing tasks for {1} build'.format(len(tasks), target))
    return tasks
