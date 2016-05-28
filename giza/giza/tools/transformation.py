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

import libgiza.task

from giza.tools.files import copy_always, copy_if_needed

logger = logging.getLogger('giza.transformation')


class ProcessingError(Exception):
    pass


def decode_lines_from_file(fn):
    with open(fn, 'r') as f:
        return [line.decode('utf-8').rstrip() for line in f.readlines()]


def encode_lines_to_file(fn, lines):
    with open(fn, 'w') as f:
        f.write('\n'.join(lines).encode('utf-8'))
        f.write('\n')


def munge_page(fn, regex, out_fn=None,  tag='build'):
    if out_fn is None:
        out_fn = fn

    page_lines = [munge_content(ln, regex) for ln in decode_lines_from_file(fn)
                  if ln is not None]

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
    if start_after is not None and end_before is not None:
        if type(start_after) != type(end_before):
            raise TypeError('start-after and end-before types must match')

    with open(fn, 'r') as f:
        source_lines = f.readlines()

    should_find_line_num = False

    if isinstance(start_after, int):
        start_idx = start_after
    else:
        # start_after is none or some string -- if string, find line num
        start_idx = 0
        if start_after is not None:
            should_find_line_num = True

    if isinstance(end_before, int):
        end_idx = end_before - 1
    else:
        # end_before is none or some string -- if string, find line num
        end_idx = len(source_lines) - 1
        if end_before is not None:
            should_find_line_num = True

    # should_find_line_num is True if:
    #  - start_after = string and end_before = string
    #  - start_after = string and end_before is None
    #  - start_after is None and end_before is string

    if should_find_line_num is True:
        for idx, ln in enumerate(source_lines):
            if start_after is not None and start_after in ln:
                start_idx = idx + 1
                if end_before is None:
                    break

            if end_before is not None and end_before in ln:
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


def process_page_task(fn, output_fn, regex, builder='processor', copy='always'):
    return libgiza.task.Task(job=_process_page,
                             args=(fn, output_fn, regex, copy, builder),
                             target=output_fn,
                             dependency=None,
                             description="modify page: ({0}, {1})".format(fn, output_fn))


def process_page(fn, output_fn, regex, app, builder='processor', copy='always'):
    t = app.add('task')
    t.job = _process_page
    t.args = [fn, output_fn, regex, copy, builder]
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
