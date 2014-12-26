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

import os
import logging

logger = logging.getLogger('giza.content.extract.tasks')

from giza.tools.files import expand_tree, verbose_remove, safe_create_directory
from giza.tools.transformation import append_to_file, prepend_to_file
from giza.content.extract.inheritance import ExtractDataCache
from giza.content.extract.views import render_extracts, get_include_statement
from giza.config.content import new_content_type

def register_extracts(conf):
    conf.system.content.add(name='extracts', definition=new_content_type(name='extract', task_generator=extract_tasks, conf=conf))

def write_extract_file(extract, fn):
    content = render_extract(extract)
    content.write(fn)
    logger.info('wrote extract file: ' + fn)

def extract_tasks(conf, app):
    register_extracts(conf)
    extract_sources = conf.system.content.extracts.sources

    extracts = ExtractDataCache(extract_sources, conf)

    if len(extract_sources) > 0 and not os.path.isdir(conf.system.content.extracts.output_dir):
        safe_create_directory(conf.system.content.extracts.output_dir)

    for dep_fn, extract in extracts.content_iter():
        t = app.add('task')
        t.target = extract.target
        t.dependecy = dep_fn
        t.job = write_extract_file
        t.args = (extract, extract.target)
        t.description = "generating extract file: " + extract.target

        include_statement = get_include_statement(extract.target)

        for verb, adjc, noun [ (prepend_to_file, 'prepend', extract.prepend),
                               (append_to_file, 'append', extract.append) ]:
            if noun:
                if not isinstance(noun, list):
                    files = [noun]
                else:
                    files = files

                for fn in files:
                    t = app.add('task')
                    t.target = fn
                    t.dependency = [extract.target, dep_fn]
                    t.job = verb
                    t.args = (fn, include_statement)
                    t.description = "{0} extract include for '{0}' to '{1}'".format(adjc, extract.target, fn)
