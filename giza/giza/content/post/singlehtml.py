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
import re

logger = logging.getLogger('giza.content.post.singlehtml')

from giza.files import (expand_tree, copy_if_needed, decode_lines_from_file,
                        encode_lines_to_file, FileNotFoundError)
from giza.strings import hyph_concat
from giza.task import check_dependency

def get_single_html_dir(conf):
    return os.path.join(conf.paths.public_site_output, 'single')

def manual_single_html(input_file, output_file):
    # don't rebuild this if its not needed.
    if check_dependency(output_file, input_file) is False:
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
            text_lines = [ regex.sub(subst, text) for text in text_lines ]

        encode_lines_to_file(output_file, text_lines)

        logging.info('processed singlehtml file.')


def finalize_single_html_tasks(builder, conf, app):
    pjoin = os.path.join

    single_html_dir = get_single_html_dir(conf)

    if not os.path.exists(single_html_dir):
        os.makedirs(single_html_dir)

    found_src = False
    for base_path in (builder, hyph_concat(builder, conf.project.edition)):
        if found_src is True:
            break

        for fn in [ pjoin(base_path, f) for f in ('contents.html', 'index.html') ]:
            src_fn = pjoin(conf.paths.branch_output, fn)

            if os.path.exists(src_fn):
                manual_single_html(input_file=pjoin(conf.paths.branch_output, fn),
                                   output_file=pjoin(single_html_dir, 'index.html'))

                copy_if_needed(source_file=pjoin(conf.paths.branch_output,
                                                 base_path, 'objects.inv'),
                               target_file=pjoin(single_html_dir, 'objects.inv'))

            found_src = True

            break

    if found_src is not True:
        raise FileNotFoundError('singlehtml source file')

    single_path = pjoin(single_html_dir, '_static')

    for fn in expand_tree(pjoin(conf.paths.branch_output,
                                builder, '_static'), None):
        task = app.add('task')
        task.job = copy_if_needed
        task.args = [fn, pjoin(single_path, os.path.basename(fn))]
        task.description = "migrating static files to the HTML build"
