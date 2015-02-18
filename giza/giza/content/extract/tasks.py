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

from giza.tools.transformation import append_to_file, prepend_to_file
from giza.content.extract.inheritance import ExtractDataCache
from giza.content.extract.views import render_extracts, get_include_statement
from giza.config.content import new_content_type
from libgiza.task import Task

logger = logging.getLogger('giza.content.extract.tasks')


def register_extracts(conf):
    content_dfn = new_content_type(name='extracts',
                                   task_generator=extract_tasks,
                                   conf=conf)

    conf.system.content.add(name='extracts', definition=content_dfn)


def write_extract_file(extract, fn):
    content = render_extracts(extract)
    content.write(fn)
    logger.info('wrote extract file: ' + fn)


def extract_tasks(conf):
    extracts = ExtractDataCache(conf.system.content.extracts.sources, conf)
    extracts.create_output_dir()

    tasks = []
    for dep_fn, extract in extracts.content_iter():
        t = Task(job=write_extract_file,
                 args=(extract, extract.target),
                 description="generating extract file: " + extract.target,
                 target=extract.target,
                 dependency=dep_fn)
        tasks.append(t)

        include_statement = get_include_statement(extract.target_project_path)

        for verb, adjc, files in [(prepend_to_file, 'prepend', extract.prepend),
                                  (append_to_file, 'append', extract.append)]:
            # have to run appends and prepends always, because the rsync that
            # populates build/<branch>/source should and does overwrite these
            # files on every source generation step. None in the dep list does this.
            for fn in files:
                msg = "{0} extract include for '{0}' to '{1}'".format(adjc, extract.target, fn)
                t = Task(job=verb,
                         args=(fn, include_statement),
                         target=fn,
                         dependency=[None, dep_fn],
                         description=msg)
                tasks.append(t)

    logger.info("added tasks for {0} extract generation tasks".format(len(tasks)))

    return tasks
