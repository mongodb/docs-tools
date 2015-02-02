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

import collections
import logging
import re

logger = logging.getLogger('giza.transformation')

from giza.tools.files import copy_always, copy_if_needed, encode_lines_to_file, decode_lines_from_file
from giza.tools.serialization import ingest_yaml_list

class ProcessingError(Exception):
    pass

def munge_page(fn, regex, out_fn=None,  tag='build'):
    if out_fn is None:
        out_fn = fn

    page_lines = [ munge_content(ln, regex) for ln in decode_lines_from_file(fn)
                   if ln is not None ]

    if len(page_lines) > 0:
        encode_lines_to_file(out_fn, page_lines)
    else:
        logger.warning('{0}: did not write {1}'.format(tag, out_fn))

def munge_content(content, regex):
    if isinstance(regex, list):
        for cregex, subst in regex:
            content = cregex.sub(subst, content)
        return content
    else:
        return regex[0].sub(regex[1], content)


def truncate_file(fn, start_after=None, end_before=None):
    with open(fn, 'r') as f:
        source_lines = f.readlines()

    start_idx = 0
    end_idx = len(source_lines) - 1

    for idx, ln in enumerate(source_lines):
        if start_after is not None:
            if start_idx == 0 and ln.startswith(start_after):
                start_idx = idx - 1
                start_after = None

        if end_before is not None:
            if ln.startswith(end_before):
                end_idx = idx
                break

    with open(fn, 'w') as f:
        f.writelines(source_lines[start_idx:end_idx])

def append_to_file(fn, text):
    with open(fn, 'a') as f:
        f.write('\n')
        f.write(text)

def prepend_to_file(fn, text):
    with open(fn, 'r') as f:
        body = f.readlines()

    with open(fn, 'w') as f:
        f.write(text)
        f.writelines(body)

def process_page(fn, output_fn, regex, app, builder='processor', copy='always'):
    t = app.add('task')
    t.job = _process_page
    t.args = [fn, output_fn, regex, copy, builder ]
    t.target = output_fn
    t.depenency = None
    t.description = "modify page"

    logger.debug('added tasks to process file: {0}'.format(fn))

def _process_page(fn, output_fn, regex, copy, builder):
    tmp_fn = fn + '~'

    munge_page(fn=fn, out_fn=tmp_fn, regex=regex)

    cp_args = dict(source_file=tmp_fn,
                   target_file=output_fn,
                   name=builder)

    if copy == 'always':
        copy_always(**cp_args)
    else:
        copy_if_needed(**cp_args)

def post_process_tasks(app, tasks=None, source_fn=None):
    """
    input documents should be:

    {
      'transform': {
                     'regex': str,
                     'replace': str
                   }
      'type': <str>
      'file': <str|list>
    }

    ``transform`` can be either a document or a list of documents.
    """

    if tasks is None:
        if source_fn is not None:
            tasks = ingest_yaml_list(source_fn)
        else:
            raise ProcessingError('[ERROR]: no input tasks or file')
    elif not isinstance(tasks, collections.Iterable):
        raise ProcessingError('[ERROR]: cannot parse post processing specification.')

    def rjob(fn, regex, type):
        page_app = app.add('app')
        process_page(fn=fn, output_fn=fn, regex=regex, app=page_app, builder=type)

    for job in tasks:
        if not isinstance(job, dict):
            raise ProcessingError('[ERROR]: invalid replacement specification.')
        elif not 'file' in job and not 'transform' in job:
            raise ProcessingError('[ERROR]: replacement specification incomplete.')

        if 'type' not in job:
            job['type'] = 'processor'

        if isinstance(job['transform'], list):
            regex = [ (re.compile(rs['regex']), rs['replace'])
                      for rs in job['transform'] ]
        else:
            regex = (re.compile(job['transform']['regex']), job['transform']['replace'])

        if not isinstance(job['file'], list):
            job['file'] = [ job['file'] ]

        for fn in job['file']:
            rjob(fn, regex, job['type'])
