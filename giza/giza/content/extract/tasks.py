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
from giza.core.task import Task

def register_extracts(conf):
    conf.system.content.add(name='extracts', definition=new_content_type(name='extracts', task_generator=extract_tasks, conf=conf))

def write_extract_file(extract, fn):
    content = render_extracts(extract)
    content.write(fn)
    logger.info('wrote extract file: ' + fn)

def extract_tasks(conf):
    extract_sources = conf.system.content.extracts.sources

    extracts = ExtractDataCache(extract_sources, conf)

    if len(extract_sources) > 0 and not os.path.isdir(conf.system.content.extracts.output_dir):
        safe_create_directory(conf.system.content.extracts.output_dir)

    tasks = []
    for dep_fn, extract in extracts.content_iter():
        t = Task(job=write_extract_file,
                 description="generating extract file: " + extract.target,
                 target=extract.target,
                 dependency=dep_fn)
        t.args = (extract, extract.target)
        tasks.append(t)

        include_statement = get_include_statement(extract.target_project_path)

        for verb, adjc, noun in [ (prepend_to_file, 'prepend', extract.prepend),
                                  (append_to_file, 'append', extract.append) ]:
            if noun:
                if not isinstance(noun, list):
                    files = [noun]
                else:
                    files = noun

                for fn in files:
                    t = Task(job=verb,
                             target=fn,
                             dependency=dep_fn,
                             description="{0} extract include for '{0}' to '{1}'".format(adjc, extract.target, fn))
                    t.args = (fn, include_statement)
                    tasks.append(t)

    logger.info("added tasks for {0} extract generation tasks".format(len(tasks)))

    return tasks
