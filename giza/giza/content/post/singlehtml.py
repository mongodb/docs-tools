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
Post-processing for Sphinx's ``singlehtml`` builder. Modifies links and
post-processes sites for projects that use ``contents.txt`` rather than
``index.txt`` as the root document.
"""

import os.path
import logging
import re

import giza.libgiza.task

from giza.tools.files import expand_tree, copy_if_needed, safe_create_directory
from giza.tools.transformation import decode_lines_from_file, encode_lines_to_file

logger = logging.getLogger('giza.content.post.singlehtml')


def get_single_html_dir(conf):
    return os.path.join(conf.paths.projectroot, conf.paths.public_site_output, 'single')


def manual_single_html(input_file, output_file):
    # don't rebuild this if its not needed.
    if giza.libgiza.task.check_dependency(output_file, input_file) is False:
        logging.info('singlehtml not changed, not reprocessing.')
        return False
    else:
        text_lines = decode_lines_from_file(input_file)

        regexes = [
            (re.compile('href="contents.html'), 'href="index.html'),
            (re.compile('name="robots" content="index"'), 'name="robots" content="noindex"'),
            (re.compile('href="genindex.html'), 'href="../genindex/')
        ]

        for regex, subst in regexes:
            text_lines = [regex.sub(subst, text) for text in text_lines]

        encode_lines_to_file(output_file, text_lines)

        logger.info('processed singlehtml file.')


def finalize_single_html(single_html_dir, artifact_dir, conf):
    for fn in [os.path.join(artifact_dir, f) for f in ('contents.html', 'index.html')]:
        src_fn = os.path.join(conf.paths.projectroot, conf.paths.branch_output, fn)

        if os.path.exists(src_fn):
            manual_single_html(input_file=src_fn,
                               output_file=os.path.join(single_html_dir, 'index.html'))

            copy_if_needed(source_file=os.path.join(artifact_dir, 'objects.inv'),
                           target_file=os.path.join(single_html_dir, 'objects.inv'))


def finalize_single_html_tasks(builder, conf):
    single_html_dir = get_single_html_dir(conf)

    # create directory when registering tasks.
    safe_create_directory(single_html_dir)
    safe_create_directory(os.path.join(single_html_dir, '_static'))

    if 'edition' in conf.project and conf.project.edition != conf.project.name:
        artifact_dir = os.path.join(conf.paths.projectroot,
                                    conf.paths.branch_output,
                                    '-'.join((builder, conf.project.edition)))
    else:
        artifact_dir = os.path.join(conf.paths.projectroot, conf.paths.branch_output, builder)

    tasks = [giza.libgiza.task.Task(job=finalize_single_html,
                                    args=(single_html_dir, artifact_dir, conf),
                                    target=True,
                                    dependency=None,
                                    description="migrating singlehtml")]

    for fn in expand_tree(os.path.join(artifact_dir, '_static'), None):
        target_fn = os.path.join(single_html_dir, '_static', os.path.basename(fn))

        tasks.append(giza.libgiza.task.Task(job=copy_if_needed,
                                            args=(fn, target_fn),
                                            target=target_fn,
                                            dependency=fn,
                                            description="moving static files to the singlehtml build"))

    return tasks
