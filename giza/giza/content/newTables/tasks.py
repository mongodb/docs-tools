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
import shutil

from libgiza.task import Task

from giza.content.newTables.inheritance import TableDataCache
from giza.content.newTables.views import render_table
from giza.config.content import new_content_type

logger = logging.getLogger('giza.content.newTables.tasks')


def register_tables(conf):
    content_dfn = new_content_type(name='newTables',
                                   task_generator=table_tasks,
                                   conf=conf)

    conf.system.content.add(name='newTables', definition=content_dfn)


def write_table(terms, fn):
    content = render_table(terms)
    content.write(fn)
    logger.info('wrote table file: ' + fn)


def table_tasks(conf):
    terms = TableDataCache(conf.system.content.newTables.sources, conf)
    terms.create_output_dir()

    tasks = []
    for fn, table_file in terms.file_iter():
        tasks.append(Task(job=write_table,
                          args=(table_file, table_file.target(fn)),
                          description="generate table for: " + fn,
                          target=table_file.target(fn),
                          dependency=fn))

    logger.info("add {0} table tasks".format(len(tasks)))
    return tasks


def step_clean(conf):
    return [Task(job=shutil.rmtree,
                 args=[conf.system.content.newTables.output_dir],
                 target=True,
                 depdency=[conf.system.content.newTables.output_dir],
                 descrption='removing {0}'.format(conf.system.content.newTables.output_dir))]
