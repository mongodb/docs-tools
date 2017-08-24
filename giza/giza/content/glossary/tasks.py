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

from giza.libgiza.task import Task

from giza.content.glossary.inheritance import GlossaryDataCache
from giza.content.glossary.views import render_glossary
from giza.config.content import new_content_type

logger = logging.getLogger('giza.content.extract.tasks')


def register_glossary(conf):
    content_dfn = new_content_type(name='glossary',
                                   task_generator=glossary_tasks,
                                   conf=conf)

    conf.system.content.add(name='glossary', definition=content_dfn)


def write_glossary(terms, fn):
    content = render_glossary(terms)
    content.write(fn)
    logger.debug('wrote glossary file: ' + fn)


def glossary_tasks(conf):
    terms = GlossaryDataCache(conf.system.content.glossary.sources, conf)
    terms.create_output_dir()

    tasks = []
    for fn, glossary_file in terms.file_iter():
        tasks.append(Task(job=write_glossary,
                          args=(glossary_file, glossary_file.target(fn)),
                          description='generate glossary for: ' + fn,
                          target=glossary_file.target(fn),
                          dependency=fn))

    logger.debug('add {0} glossary tasks'.format(len(tasks)))
    return tasks


def glossary_clean(conf):
    return [Task(job=shutil.rmtree,
                 args=[conf.system.content.glossary.output_dir],
                 target=True,
                 dependency=[conf.system.content.glossary.output_dir],
                 description='removing {0}'.format(conf.system.content.glossary.output_dir))]
