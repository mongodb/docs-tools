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
Post processing of the output of the Sphinx manpage output. Used to get proper
fully qualified links and fix flaws in the output.
"""

import re
import os
import logging

import giza.libgiza.task

from giza.tools.files import expand_tree

logger = logging.getLogger('giza.content.manpages')

# Manpage Processing

# this is a precursor to giza.tools.transformation and should be re-implemented.


def manpage_url(regex_obj, input_file):
    with open(input_file, 'r') as f:
        manpage = f.read()

    if isinstance(regex_obj, list):
        for regex, subst in regex_obj:
            manpage = regex.sub(subst, manpage)
    else:
        manpage = regex_obj[0].sub(regex_obj[1], manpage)

    with open(input_file, 'w') as f:
        f.write(manpage)

    logger.info("fixed urls in {0}".format(input_file))


def manpage_url_tasks(builder, conf):
    project_source = os.path.join(conf.paths.projectroot,
                                  conf.paths.source)

    top_level_items = set()
    for fs_obj in os.listdir(project_source):
        if fs_obj.startswith('.static') or fs_obj == 'index.txt':
            continue
        if os.path.isdir(os.path.join(project_source, fs_obj)):
            top_level_items.add(fs_obj)
        if fs_obj.endswith('.txt'):
            top_level_items.add(fs_obj[:-4])

    top_level_items = '/' + r'[^\s]*|/'.join(top_level_items) + r'[^\s]*'

    re_string = r'(\\fB({0})\\fP)'.format(top_level_items).replace(r'-', r'\-')
    subst = conf.project.url + '/' + conf.project.tag + r'\2'

    regex_obj = (re.compile(re_string), subst)

    tasks = []
    for manpage in expand_tree(os.path.join(conf.paths.projectroot,
                                            conf.paths.output,
                                            conf.git.branches.current,
                                            builder), ['1', '5']):

        description = 'processing urls in manpage file: {0}'.format(manpage)
        tasks.append(giza.libgiza.task.Task(job=manpage_url,
                                            args=(regex_obj, manpage),
                                            target=manpage,
                                            dependency=None,
                                            description=description))

    return tasks
