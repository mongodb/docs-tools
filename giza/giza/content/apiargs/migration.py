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

import re
import logging
import os
import copy
import difflib

logger = logging.getLogger('giza.content.apiargs.migration')

from giza.tools.serialization import ingest_yaml_list, write_yaml, literal_str
from giza.tools.strings import hyph_concat
from giza.tools.transformation import munge_page
from giza.tools.files import expand_tree, safe_create_directory, rm_rf, verbose_remove
from giza.core.task import Task

def task(task, conf):
    if task == 'source':
        legacy_tables = expand_tree(os.path.join(conf.paths.projectroot, conf.paths.source, 'reference'), 'yaml')
        dirname = os.path.join(conf.paths.projectroot, conf.paths.includes, 'apiargs')
        safe_create_directory(dirname)
        offset = len(os.path.join(conf.paths.projectroot, conf.paths.source))
    elif task == 'branch':
        legacy_tables = expand_tree(os.path.join(conf.paths.projectroot, conf.paths.branch_source, 'reference'), 'yaml')
        safe_create_directory(conf.system.content.apiargs.output_dir)
        offset = len(os.path.join(conf.paths.projectroot, conf.paths.branch_source))
    else:
        logger.critical('cannot perform apiarg migration for: ' + str(task))
        return

    new_records = []
    new_basenames = []
    new_fns = []
    old_fns = []

    for fn in legacy_tables:
        new_data, new_fn = migrate_legacy_apiarg(task, fn, conf)
        if new_fn in new_fns:
            logger.error("duplicate: {0}, from: {1}".format(os.path.basename(new_fn), os.path.basename(fn)))
        else:
            new_basenames.append(new_fn[offset:])
            new_fns.append(new_fn)
            new_records.append(new_data)
            old_fns.append(fn)

    task_maker = zip(new_basenames, new_records, old_fns, new_fns)

    for basename, data, old_fn, new_fn in task_maker:
        write_yaml(data, new_fn)
        if task == 'source':
            verbose_remove(old_fn)

    new_sources = conf.system.content.apiargs.sources

    if len(new_sources) != len(legacy_tables) and len(legacy_tables) != len(new_fns):
        logger.critical('problem in apiargs table migration.')
    else:
        logger.info('legacy apiargs tables migrated successfully.')

    legacy_tables = [ fn[offset:] for fn in legacy_tables ]
    return zip(legacy_tables, new_basenames)

def migrate_legacy_apiarg(task, fn, conf, silent=False):
    legacy_data = ingest_yaml_list(fn)

    new_data, meta = transform_data(task, legacy_data, fn[len(os.path.join(conf.paths.projectroot, conf.paths.branch_output))+1:], silent, conf)

    old_base = os.path.basename(fn)
    if not old_base.startswith(meta['operation']):
        meta['operation'] = old_base[:-5].split('-', 1)[0]

    tag = old_base[:-5][len(meta['operation'])+1:]
    if tag.startswith('-'):
        tag = tag[1:]
    if tag == 'fields':
        tag = 'field'

    new_fn_base = hyph_concat('apiargs', meta['interface'], meta['operation'], tag)
    new_fn_base = new_fn_base + '.yaml'

    if task == 'source':
        new_fn = os.path.join(conf.paths.projectroot,
                              conf.paths.includes,
                              new_fn_base)
    elif task =='branch':
        new_fn = os.path.join(conf.paths.projectroot,
                              conf.paths.branch_includes,
                              new_fn_base)
    return new_data, new_fn

def transform_data(task, data, fn, silent, conf):
    output = []

    meta = {}
    for doc in data:
        if 'object' not in doc:
            if 'file' not in doc:
                print(doc)
                logger.error("error in: " + fn)
            else:
                operation = os.path.basename(fn).split('-')[0]
                if 'method' in fn:
                    meta['interface'] = 'method'
                    meta['operation'] = operation
                elif 'command' in fn:
                    meta['interface'] = 'dbcommand'
                    meta['operation'] = operation
                elif 'aggregation' in fn:
                    meta['interface'] = 'pipeline'
                    meta['operation'] = operation
                else:
                    logger.error("invalid document format in: " + fn)

                new_doc = copy.copy(meta)

                src_file = doc['file']
                if src_file.startswith('/'):
                    src_file = src_file[1:]

                if task == 'source':
                    src_file = os.path.join(conf.paths.projectroot, conf.paths.source, src_file)
                elif task == 'branch':
                    src_file = os.path.join(conf.paths.projectroot, conf.paths.branch_source, src_file)

                _, new_fn = migrate_legacy_apiarg(task, src_file, conf, True)

                new_doc.update({ 'source': { 'file': os.path.basename(new_fn), 'ref': doc['name']}})
                output.append(new_doc)

            continue

        if doc['object']['name'].endswith('()'):
            doc['object']['name'] = doc['object']['name'][:-2]
        if 'field' not in doc:
            doc['field'] = {'optional': False, 'type': 'param'}

        if silent is False and ('interface' in meta and meta['interface'] != doc['object']['type']):
            logger.warning("interface type (cmd, method) values do not agree in: " + fn)
        meta['interface'] = doc['object']['type']

        if silent is False and ('operation' in meta and meta['operation'] != doc['object']['name']):
            logger.warning("calling operation names do not agree in: " + fn)
        meta['operation'] = doc['object']['name']

        if silent is False and ('arg_name' in meta and meta['arg_name'] != doc['field']['type']):
            logger.warning('argument types do not agree in: ' + fn)
        meta['arg_name'] = doc['field']['type']

        new_doc = copy.copy(meta)
        if 'optional' in doc['field']:
            new_doc['optional'] = doc['field']['optional']

        for field_name in ('name', 'type', 'position', 'description'):
            if field_name in doc:
                if field_name == 'description':
                    new_doc[field_name] = literal_str(doc[field_name])
                else:
                    new_doc[field_name] = doc[field_name]

        output.append(new_doc)

    return output, meta

def file_munge_tasks(name_changes, loc, conf):
    tasks = []

    if loc == 'branch':
        return tasks

    name_changes = [
        (old.replace('.yaml', '.rst'), new.replace('apiargs-', 'apiargs/').replace('.yaml', '.rst'))
        for old, new in name_changes
    ]

    if loc == 'source':
        ref_files = expand_tree(os.path.join(conf.paths.projectroot, conf.paths.source, 'reference'), 'txt')
    elif loc == 'branch':
        ref_files = expand_tree(os.path.join(conf.paths.projectroot, conf.paths.branch_source, 'reference'), 'txt')

    for old, new in name_changes:
        re_pattern = (re.compile(r'include:: ' + old), r'include:: ' + new)

        for ref_file in ref_files:
            t = Task(job=munge_page,
                     args=dict(fn=ref_file,
                               regex=re_pattern),
                     target=ref_file,
                     dependency=None,
                     description='munging reference page')
            tasks.append(t)

    return tasks
