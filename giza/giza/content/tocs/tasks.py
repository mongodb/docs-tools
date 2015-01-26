# Copyright 2015 MongoDB, Inc.
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
import os.path

logger = logging.getLogger('giza.content.tocs.tasks')

from giza.content.tocs.inheritance import TocDataCache
from giza.content.tocs.views import render_toctree, render_dfn_list, render_toc_table
from giza.tools.files import safe_create_directory
from giza.tools.strings import hyph_concat
from giza.config.content import new_content_type
from giza.core.task import Task

def register_toc(conf):
    definition = new_content_type(name='toc',
                                  task_generator=toc_tasks,
                                  conf=conf,
                                  prefixes=['toc', 'ref-toc'])

    conf.system.content.add(name='toc', definition=definition)

def write_toc_tree_output(fn, toc_items):
    content = render_toctree(toc_items)
    content.write(fn)
    logger.info("wrote toctree to: " + fn)

def write_dfn_list_output(fn, toc_items):
    content = render_dfn_list(toc_items)
    content.write(fn)
    logger.info("wrote toc dfnlist to: " + fn)

def write_toc_table(fn, toc_items):
    content = render_toc_table(toc_items)
    content.write(fn)
    logger.info("wrote toc table to: " + fn)

def toc_tasks(conf):
    toc_sources = conf.system.content.toc.sources

    tocs = TocDataCache(toc_sources, conf)

    if len(toc_sources) > 0 and not os.path.isdir(conf.system.content.toc.output_dir):
        safe_create_directory(conf.system.content.toc.output_dir)

    tasks = []
    for dep_fn, toc_data in tocs.file_iter():
        if 'ref-toc-' in dep_fn:
            base_offset = 8
        else:
            base_offset = 4

        fn_basename = os.path.basename(dep_fn)[base_offset:].replace('yaml', 'rst')

        toc_items = toc_data.ordered_items()

        if toc_data.is_spec() is False:
            out_fn = os.path.join(conf.system.content.toc.output_dir, fn_basename)
            t = Task(job=write_toc_tree_output,
                     target=out_fn,
                     dependency=dep_fn,
                     description="writing toctree to '{0}'".format(out_fn))
            t.args = (out_fn, toc_items)
            tasks.append(t)

        if 'ref-toc' in dep_fn:
            out_fn = os.path.join(conf.system.content.toc.output_dir, hyph_concat('table', fn_basename))

            reft = Task(job=write_toc_table,
                        target=out_fn,
                        dependency=dep_fn,
                        description="write table of contents generator".format(out_fn))
            reft.args = (out_fn, toc_items)
            tasks.append(reft)
        else:
            out_fn = os.path.join(conf.system.content.toc.output_dir, hyph_concat('dfn-list', fn_basename))
            dt = Task(job=write_dfn_list_output,
                      target=out_fn,
                      dependency=dep_fn,
                      description="write definition list toc to '{0}'".format(out_fn))
            dt.args = (out_fn, toc_items)
            tasks.append(dt)

    logger.info('added tasks for {0} toc generation tasks'.format(len(tasks)))

    return tasks
