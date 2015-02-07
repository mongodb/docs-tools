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
Post-process all output produced by JSON to add a "text" field to these
documents that omits the XML data injected into this format by default so that
search tools can use this data to index content. Also generates a file with a
list of paths in the output.
"""

import json
import logging
import os
import re
import subprocess

import libgiza.task

from giza.tools.files import expand_tree, copy_if_needed, safe_create_directory
from giza.tools.transformation import munge_content

logger = logging.getLogger('giza.content.post.json_output')

# Process Sphinx Json Output


def json_output(conf):
    list_file = os.path.join(conf.paths.branch_output, 'json-file-list')
    public_list_file = os.path.join(conf.paths.projectroot,
                                    conf.paths.public_site_output,
                                    'json', '.file_list')

    cmd = ('rsync --recursive --times --delete '
           '--exclude="*pickle" --exclude=".buildinfo" --exclude="*fjson" '
           '{src} {dst}')

    json_dst = os.path.join(conf.paths.projectroot, conf.paths.public_site_output, 'json')
    safe_create_directory(json_dst)

    builder = 'json'
    if 'edition' in conf.project and conf.project.edition != conf.project.name:
        builder += '-' + conf.project.edition

    cmd_str = cmd.format(src=os.path.join(conf.paths.projectroot,
                                          conf.paths.branch_output, builder) + '/',
                         dst=json_dst)

    try:
        subprocess.check_call(cmd_str.split())
        copy_if_needed(list_file, public_list_file)
        logger.info('deployed json files to local staging.')
    except subprocess.CalledProcessError:
        logger.error('error migrating json artifacts to local staging')


def json_output_tasks(conf):
    regexes = [
        (re.compile(r'<a class=\"headerlink\"'), '<a'),
        (re.compile(r'<[^>]*>'), ''),
        (re.compile(r'&#8220;'), '"'),
        (re.compile(r'&#8221;'), '"'),
        (re.compile(r'&#8216;'), "'"),
        (re.compile(r'&#8217;'), "'"),
        (re.compile(r'&#\d{4};'), ''),
        (re.compile(r'&nbsp;'), ''),
        (re.compile(r'&gt;'), '>'),
        (re.compile(r'&lt;'), '<')
    ]

    outputs = []

    tasks = []

    for fn in expand_tree('source', 'txt'):
        # path = build/<branch>/json/<filename>

        if 'edition' in conf.project and conf.project.edition != conf.project.name:
            path = os.path.join(conf.paths.branch_output,
                                'json-' + conf.project.edition,
                                os.path.splitext(fn.split(os.path.sep, 1)[1])[0])

        else:
            path = os.path.join(conf.paths.branch_output,
                                'json', os.path.splitext(fn.split(os.path.sep, 1)[1])[0])

        fjson = path + '.fjson'
        jsonf = path + '.json'

        task = libgiza.task.Task(job=process_json_file,
                                 args=(fjson, jsonf, regexes, conf),
                                 target=jsonf,
                                 dependency=fjson,
                                 description="processing json file".format(json))
        tasks.append(task)
        outputs.append(jsonf)

    list_file = os.path.join(conf.paths.branch_output, 'json-file-list')
    tasks.append(libgiza.task.Task(job=generate_list_file,
                                   args=(outputs, list_file, conf),
                                   target=list_file,
                                   dependency=None,
                                   description="generating list of json files"))

    transfer = libgiza.task.Task(job=json_output,
                                 args=[conf],
                                 target=True,
                                 dependency=None,
                                 description='transfer json output to public directory')

    return tasks, transfer


def process_json_file(input_fn, output_fn, regexes, conf=None):
    if os.path.isfile(input_fn) is False:
        return False

    with open(input_fn, 'r') as f:
        document = f.read()

    doc = json.loads(document)

    if 'body' in doc:
        text = doc['body'].encode('ascii', 'ignore')
        text = munge_content(text, regexes)

        doc['text'] = ' '.join(text.split('\n')).strip()

    if 'title' in doc:
        title = doc['title'].encode('ascii', 'ignore')
        title = munge_content(title, regexes)

        doc['title'] = title

    url = get_site_url(conf)
    url.extend(input_fn.rsplit('.', 1)[0].split(os.path.sep)[3:])
    doc['url'] = '/'.join(url) + '/'

    with open(output_fn, 'w') as f:
        f.write(json.dumps(doc))

    return True


def generate_list_file(outputs, path, conf):
    dirname = os.path.dirname(path)
    safe_create_directory(dirname)

    url = get_site_url(conf)
    url.append('json')
    url = '/'.join(url)

    with open(path, 'w') as f:
        for fn in outputs:
            if os.path.isfile(fn) is True:
                line = '/'.join([url, fn.split('/', 3)[3:][0]])
                f.write(line)
                f.write('\n')

    logger.info('rebuilt inventory of json output.')


def get_site_url(conf):
    url = [conf.project.url]

    if conf.project.basepath not in ('', None):
        url.append(conf.project.basepath)

    if conf.project.branched is True and 'editions' in conf.project:
        url.append(conf.git.branches.current)

    return url
