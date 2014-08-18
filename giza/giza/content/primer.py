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

logger = logging.getLogger('giza.content.primer')

from giza.tools.files import copy_if_needed, copy_always, expand_tree, verbose_remove
from giza.tools.serialization import ingest_yaml_list
from giza.tools.transformation import post_process_tasks, truncate_file, append_to_file

def get_migration_specifications(conf):
    return [ fn for fn in expand_tree(os.path.join(conf.paths.projectroot,
                                                   conf.paths.builddata))
             if  conf.project.name in os.path.basename(fn) and 'migrations' in fn ]

def convert_multi_source(page):
    if 'source_dir' in page:
        return [ { 'source': source, 'source_dir': page['source_dir'] }
                 for source in page['sources'] ]
    else:
        return [ { 'source': source }
                 for source in page['sources'] ]

def fix_migration_paths(page):
    if 'target' not in page:
        page['target'] = page['source']

    if page['target'].endswith('.txt'):
        msg = '({0}) imported files cannot end with ".txt", changing to ".rst"'
        logger.warning(msg.format(page['source']))
        page['target'] = page['target'].replace('.txt', '.rst')

    for field  in ['source', 'target']:
        if page[field].startswith('/'):
            page[field] = page[field][1:]

    return page

def clean(conf):
    "Removes all migrated primer files according to the current spec."

    migration_paths = get_migration_specifications(conf)
    migrations = ingest_yaml_list(*migration_paths)

    targets = []
    for page in migrations:
        if 'sources' in page:
            migrations.extend(convert_multi_source(page))
            continue

        page = fix_migration_paths(page)

        targets.append(os.path.join(conf.paths.projectroot, conf.paths.source, page['target']))

    map(verbose_remove, targets)
    logger.info('clean: removed {0} files'.format(len(targets)))

def primer_migration_tasks(conf, app):
    "Migrates all manual files to primer according to the spec. As needed."

    migration_paths = get_migration_specifications(conf)

    if len(migration_paths) == 0:
        return False
    else:
        migrations = ingest_yaml_list(*migration_paths)

        munge_jobs = []
        for page in migrations:
            if 'sources' in page:
                migrations.extend(convert_multi_source(page))
                continue

            page = fix_migration_paths(page)

            fq_target = os.path.join(conf.paths.projectroot, conf.paths.source, page['target'])
            if 'source_dir' in page:
                fq_source = os.path.abspath(os.path.join(conf.paths.projectroot, page['source_dir'], page['source']))
            else:
                fq_source = os.path.abspath(os.path.join(conf.paths.projectroot, '..', 'source', page['source']))

            prev = build_migration_task(fq_target, fq_source, app)

            if 'truncate' in page:
                build_truncate_task(page['truncate'], fq_target, app)

            if 'transform' in page:
                prev.job = copy_always
                munge_jobs.append(build_transform_task(page['transform'], fq_target, app))

            if 'append' in page:
                prev.job = copy_always
                build_append_task(page, fq_target, migration_paths, app)

        post_process_tasks(app=app, tasks=munge_jobs)
        msg = 'added {0} migration jobs'.format(len(migrations))

        logger.info(msg)

        return True

def build_migration_task(target, source, app):
    task = app.add('task')
    task.target = target
    task.job = copy_if_needed
    task.args = [ source, target, 'primer' ]

    return task

def build_transform_task(transform, target, app):
    return {
        'file': target,
        'type': 'primer-processing',
        'transform': transform
    }

def build_append_task(page, target, spec_files, app):
    task = app.add('task')
    task.target = page['target']
    task.job = append_to_file
    task.args = [ target, page['append'] ]
    task.dependency = spec_files

def build_truncate_task(truncate_spec, target, app):
    task = app.add('task')
    task.target = target
    task.job = truncate_file
    task.args = {
        'fn': target,
        'start_after': truncate_spec['start-after'] if 'start-after' in truncate_spec else None,
        'end_before': truncate_spec['end-before'] if 'end-before' in truncate_spec else None
    }
