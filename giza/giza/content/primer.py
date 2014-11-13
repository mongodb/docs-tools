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
Content migration and transformation engine that makes it possible to import and
reuse content from repository, or project in another. Migration specifications
can also include transformation specifications to trim content from a source
file, append content to a file, or apply a regular expression substitution.

Developed for the Primer/Getting Started section. Configuration files are all
``.yaml`` files in the *config* directory that have the substring "migration" in
them. Uses the functions in :mod:`giza.tools.transformation` and
:mod:`giza.tools.files` to perform the action, and just adds migration and
transformation tasks to a :class:`giza.core.app.BuildApp()` instance.
"""

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

def directory_expansion(source_path, page, conf):
    new_page = { 'sources': expand_tree(source_path, None)}
    del page['source']

    if 'source_dir' in page:
        new_page['source_dir'] = page['source_dir']

    pages = []

    for p in convert_multi_source(new_page):
        p.update(page)
        p['target'] = os.path.join(conf.paths.projectroot,
                                   conf.paths.source,
                                   p['target'],
                                   p['source'][len(source_path)+1:])

        pages.append(p)


    return pages

def convert_multi_source(page):
    pages = [ { 'source': source }
              for source in page['sources'] ]

    for k in ('source', 'sources'):
        if k in page:
            del page[k]

    r = []
    for p in pages:
        p.update(page)
        r.append(p)

    return r


########## Path Normalization Helper Functions

def fix_migration_paths(page):
    if 'target' not in page:
        page['target'] = page['source']

    if 'override' not in page:
        page['override'] = True

    if page['target'].endswith('.txt') and page['override'] is True:
        msg = '({0}) imported files cannot end with ".txt", changing to ".rst"'
        logger.warning(msg.format(page['source']))
        page['target'] = page['target'].replace('.txt', '.rst')

    return page

def trim_leading_slash_from_pages(page):
    for field  in ['source', 'target']:
        if page[field].startswith('/'):
            page[field] = page[field][1:]

    return page

def resolve_page_path(page, conf):
    if page['target'].startswith('/'):
        fq_target = page['target']
    elif '{root}' in page['target']:
        fq_target = page['target'].format(root=conf.paths.projectroot)
    else:
        fq_target = os.path.join(conf.paths.projectroot, conf.paths.source, page['target'])

    if page['source'].startswith('/'):
        fq_source = page['source']
    elif 'source_dir' in page:
        fq_source = os.path.abspath(os.path.join(conf.paths.projectroot, page['source_dir'], page['source']))
    else:
        fq_source = os.path.abspath(os.path.join(conf.paths.projectroot, '..', 'source', page['source']))

    return fq_target, fq_source

########## Main Migration Operations and Task Generator

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
            fq_target, fq_source = resolve_page_path(page, conf)

            if page['source'].endswith('/'):
                migrations.extend(directory_expansion(fq_source, page, conf))
                continue

            page = trim_leading_slash_from_pages(page)
            prev = build_migration_task(fq_target, fq_source, app)

            if 'truncate' in page:
                build_truncate_task(page['truncate'], fq_target, fq_source, app)

            if 'transform' in page:
                prev.job = copy_always
                munge_jobs.append(build_transform_task(page['transform'], fq_target))

            if 'append' in page:
                prev.job = copy_always
                build_append_task(page, fq_target, migration_paths, app)

        post_process_tasks(app=app, tasks=munge_jobs)
        msg = 'added {0} migration jobs'.format(len(migrations))

        logger.info(msg)

        return True


########## Task Creators

def clean(conf, app):
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

    t = app.add('map')
    t.job = verbose_remove
    t.iter = targets
    t.description = 'clean primer migrations'

    logger.info('clean: removed {0} files'.format(len(targets)))

def build_migration_task(target, source, app):
    task = app.add('task')
    task.target = target
    task.job = copy_if_needed
    task.target = target
    task.dependency = source
    task.args = [ source, target, 'primer' ]

    return task

def build_transform_task(transform, target):
    return {
        'file': target,
        'type': 'primer-processing',
        'transform': transform
    }

def build_append_task(page, target, spec_files, app):
    task = app.add('task')
    task.target = page['target']
    task.dependency = spec_files
    task.job = append_to_file
    task.args = [ target, page['append'] ]

def build_truncate_task(truncate_spec, target, deps, app):
    task = app.add('task')
    task.target = target
    task.dependency = deps
    task.job = truncate_file
    task.args = {
        'fn': target,
        'start_after': truncate_spec['start-after'] if 'start-after' in truncate_spec else None,
        'end_before': truncate_spec['end-before'] if 'end-before' in truncate_spec else None
    }
