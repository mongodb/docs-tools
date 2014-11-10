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

logger = logging.getLogger('giza.content.post.singlehtml')

from giza.core.task import check_dependency
from giza.tools.strings import hyph_concat
from giza.tools.files import (expand_tree, copy_if_needed, decode_lines_from_file,
                              encode_lines_to_file, FileNotFoundError, safe_create_directory)

def get_single_html_dir(conf):
    return os.path.join(conf.paths.projectroot, conf.paths.public_site_output, 'single')

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

# TODO: convert this to use common infrastructure in giza.tools.transformations.
def finalize_single_html_tasks(builder, conf, app):
    single_html_dir = get_single_html_dir(conf)

    safe_create_directory(single_html_dir)

    found_src = False
    for base_path in (builder, hyph_concat(builder, conf.project.edition)):
        if found_src is True:
            break

        for fn in [ os.path.join(base_path, f) for f in ('contents.html', 'index.html') ]:
            src_fn = os.path.join(conf.paths.projectroot, conf.paths.branch_output, fn)

            if os.path.exists(src_fn):
                manual_single_html(input_file=src_fn,
                                   output_file=os.path.join(single_html_dir, 'index.html'))

                copy_if_needed(source_file=os.path.join(conf.paths.projectroot,
                                                 conf.paths.branch_output,
                                                 base_path, 'objects.inv'),
                               target_file=os.path.join(single_html_dir, 'objects.inv'))

                found_src = True

                break

    if found_src is not True:
        raise FileNotFoundError('singlehtml source file')

    single_path = os.path.join(single_html_dir, '_static')

    for fn in expand_tree(os.path.join(os.path.dirname(src_fn), '_static'), None):
        target_fn = os.path.join(single_path, os.path.basename(fn))

        task = app.add('task')
        task.job = copy_if_needed
        task.target = target_fn
        task.dependency = fn
        task.args = [fn, target_fn]
        task.description = "migrating static files to the HTML build"
