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

import json
import re
import os
import logging

logger = logging.getLogger('giza.content.post.json_output')

from giza.tools.command import command
from giza.tools.strings import dot_concat
from giza.tools.files import expand_tree, copy_if_needed
from giza.tools.transformation import munge_content

########## Process Sphinx Json Output ##########

def json_output(conf):
    list_file = os.path.join(conf.paths.branch_output, 'json-file-list')
    public_list_file = os.path.join(conf.paths.public_site_output,
                                    'json', '.file_list')

    cmd = 'rsync --recursive --times --delete --exclude="*pickle" --exclude=".buildinfo" --exclude="*fjson" {src} {dst}'

    json_dst = os.path.join(conf.paths.public_site_output, 'json')

    if not os.path.exists(json_dst):
        logger.debug('created directories for {0}'.format(json_dst))
        os.makedirs(json_dst)

    builder = 'json'
    if 'edition' in conf.project and conf.project.edition != conf.project.name:
        builder += '-' + conf.project.edition

    command(cmd.format(src=os.path.join(conf.paths.branch_output, builder) + '/',
                       dst=json_dst))

    copy_if_needed(list_file, public_list_file)
    logger.info('deployed json files to local staging.')

def json_output_tasks(conf, app):
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
    for fn in expand_tree('source', 'txt'):
        # path = build/<branch>/json/<filename>

        if 'edition' in conf.project and conf.project.edition != conf.project.name:
            path = os.path.join(conf.paths.branch_output,
                                'json-' + conf.project.edition, 
                                os.path.splitext(fn.split(os.path.sep, 1)[1])[0])
            
        else:
            path = os.path.join(conf.paths.branch_output,
                                'json', os.path.splitext(fn.split(os.path.sep, 1)[1])[0])



        fjson = dot_concat(path, 'fjson')
        json = dot_concat(path, 'json')

        # skip files that are excluded. trust sphinx to produce needed files
        # correctly.
        if not os.path.isfile(fjson):
            continue
        else:
            task = app.add('task')
            task.target = json
            task.dependency = fjson
            task.job = process_json_file
            task.description = "processing json file".format(json)
            task.args = [fjson, json, regexes, conf]

            outputs.append(json)

    list_file = os.path.join(conf.paths.branch_output, 'json-file-list')

    list_task = app.add('task')
    list_task.target = list_file
    list_task.job = generate_list_file
    list_task.args = [outputs, list_file, conf]

    output = app.add('app')
    out_task = output.add('task')
    out_task.job = json_output
    out_task.args = [conf]
    out_task.description = 'transfer json output to public directory'

def process_json_file(input_fn, output_fn, regexes, conf=None):
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

    url = [ conf.project.url, conf.project.basepath ]
    url.extend(input_fn.rsplit('.', 1)[0].split(os.path.sep)[3:])

    doc['url'] = '/'.join(url) + '/'

    with open(output_fn, 'w') as f:
        f.write(json.dumps(doc))

def generate_list_file(outputs, path, conf):
    dirname = os.path.dirname(path)

    url = '/'.join([ conf.project.url, conf.project.basepath, 'json' ])

    if not os.path.exists(dirname):
        os.mkdir(dirname)

    with open(path, 'w') as f:
        for fn in outputs:
            f.write( '/'.join([ url, fn.split('/', 3)[3:][0]]) )
            f.write('\n')

    logger.info('rebuilt inventory of json output.')
