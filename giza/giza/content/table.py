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
Generate ``rst`` tables from ``yaml`` files in the ``source/includes`` directory
that begin with ``table-``. Uses the table builder capacity in the
:mod:`rstcloth.table` module.

Legacy implementation.
"""

import os.path
import logging

import libgiza.task

from rstcloth.table import TableBuilder, YamlTable, ListTable
from giza.tools.files import expand_tree, verbose_remove, safe_create_directory

logger = logging.getLogger('giza.content.table')

# Table Builder


def _get_table_output_name(fn):
    base, leaf = os.path.split(os.path.splitext(fn)[0])

    return os.path.join(base, 'table', leaf[6:]) + '.rst'


def _get_list_table_output_name(fn):
    base, leaf = os.path.split(os.path.splitext(fn)[0])

    return ''.join((os.path.join(base, 'table', leaf[6:]), '-list', '.rst'))


def make_parent_dirs(*paths):
    for path in paths:
        safe_create_directory(os.path.dirname(path))


def _generate_tables(source, target, list_target):
    table_data = YamlTable(source)

    make_parent_dirs(target, list_target)

    # if not table_data.format or table_data.format is None:
    #     build_all = True

    list_table = TableBuilder(ListTable(table_data))
    list_table.write(list_target)
    logger.debug('rebuilt rendered table {0}'.format(list_target))

    list_table.write(target)
    logger.debug('rebuilt rendered list table {0}'.format(target))

    # if build_all or table_data.format == 'list':
    #     list_table = TableBuilder(ListTable(table_data))
    #     list_table.write(list_target)
    #     print('[table]: rebuilt {0}'.format(list_target))
    # if build_all or table_data.format == 'rst':
    #     # this really ought to be RstTable, but there's a bug there.
    #     rst_table = TableBuilder(ListTable(table_data))
    #     rst_table.write(target)

    #     print('[table]: rebuilt {0} as (a list table)'.format(target))

    logger.info('rebuilt rendered table output for {0}'.format(source))


# Table Source Iterators

def table_sources(conf):
    path = os.path.join(conf.paths.projectroot, conf.paths.branch_includes)

    for source in expand_tree(path, 'yaml'):
        if os.path.basename(source).startswith('table'):
            yield source

# Table Tasks


def table_tasks(conf):
    tasks = []
    for source in table_sources(conf):
        target = _get_table_output_name(source)
        list_target = _get_list_table_output_name(source)

        description = 'generating tables: {0}, {1} from'.format(target, list_target, source)
        tasks.append(libgiza.task.Task(job=_generate_tables,
                                       args=(source, target, list_target),
                                       target=[target, list_target],
                                       dependency=source,
                                       description=description))

        logger.debug('adding table job to build: {0}'.format(target))

    return tasks


def table_clean(conf):
    tasks = []
    for source in table_sources(conf):
        tasks.extend([libgiza.task.Task(job=verbose_remove,
                                        args=[_get_table_output_name(source)]),
                      libgiza.task.Task(job=verbose_remove,
                                        args=[_get_list_table_output_name(source)])])

    return tasks
