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
transformation tasks to a :class:`libgiza.app.BuildApp()` instance.
"""

import os
import logging
import re

import yaml
import libgiza.task

from giza.tools.files import copy_if_needed, copy_always, expand_tree, verbose_remove
from giza.tools.transformation import process_page, truncate_file, append_to_file

logger = logging.getLogger('giza.content.primer')


def get_migration_specifications(conf):
    output = []
    files = [fn for fn in expand_tree(os.path.join(conf.paths.projectroot,
                                                   conf.paths.builddata))
             if conf.project.name in os.path.basename(fn) and 'migrations' in fn]

    for migration_spec in files:
        with open(migration_spec, 'r') as f:
            output.extend(yaml.safe_load_all(f))

    return files, output


def directory_expansion(source_path, page, conf):
    new_page = {'sources': expand_tree(source_path, None)}
    del page['source']

    if 'source_dir' in page:
        new_page['source_dir'] = page['source_dir']

    pages = []

    for p in convert_multi_source(new_page):
        p.update(page)
        p['target'] = os.path.join(conf.paths.projectroot,
                                   conf.paths.source,
                                   p['target'],
                                   p['source'][len(source_path) + 1:])

        pages.append(p)

    return pages


def convert_multi_source(page):
    pages = [{'source': source}
             for source in page['sources']]

    for k in ('source', 'sources'):
        if k in page:
            del page[k]

    r = []
    for p in pages:
        p.update(page)
        r.append(p)

    return r


# Path Normalization Helper Functions

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
    for field in ['source', 'target']:
        if page[field].startswith('/'):
            page[field] = page[field][1:]

    return page


def resolve_page_path(page, conf):
    if page['target'].startswith('/'):
        fq_target = page['target']
    elif '{' in page['target'] and '}' in page['target']:
        fq_target = page['target']
        if '{root}' in fq_target:
            fq_target = fq_target.format(root=conf.paths.projectroot)
        if '{branch}' in fq_target:
            fq_target = fq_target.format(branch=conf.git.brancehs.current)
    else:
        fq_target = os.path.join(conf.paths.projectroot, conf.paths.source, page['target'])

    if page['source'].startswith('/'):
        fq_source = page['source']
    elif 'source_dir' in page:
        fq_source = os.path.abspath(os.path.join(conf.paths.projectroot,
                                                 page['source_dir'],
                                                 page['source']))
    else:
        fq_source = os.path.abspath(os.path.join(conf.paths.projectroot,
                                                 '..', conf.paths.source,
                                                 page['source']))

    return fq_target, fq_source

# Main Migration Operations and Task Generator


def primer_migration_tasks(conf):
    "Migrates all manual files to primer according to the spec. As needed."

    files, migrations = get_migration_specifications(conf)

    if len(migrations) == 0:
        return []

    tasks = []
    sub_tasks = []

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
        prev = build_migration_task(fq_target, fq_source)
        tasks.append(prev)

        if 'truncate' in page:
            t = build_truncate_task(page['truncate'], fq_target, fq_source)
            tasks.append(t)

        if 'transform' in page:
            prev.job = copy_always

            if not isinstance(page['transform'], list):
                page['transform'] = [page['transform']]

            process_task = process_page(fn=fq_target,
                                        output_fn=fq_target,
                                        regex=[(re.compile(rs['regex']), rs['replace'])
                                               for rs in page['transform']],
                                        builder='primer-processing')
            sub_tasks.append(process_task)

        if 'append' in page:
            prev.job = copy_always

            t = build_append_task(page, fq_target, files)
            tasks.append(t)

    if len(sub_tasks) > 0:
        tasks.append(sub_tasks)

    msg = 'added {0} migration jobs'.format(len(migrations))
    logger.info(msg)

    return tasks


# Task Creators

def clean(conf):
    "Removes all migrated primer files according to the current spec."

    _, migrations = get_migration_specifications(conf)

    tasks = []

    for page in migrations:
        if 'sources' in page:
            migrations.extend(convert_multi_source(page))
            continue

        page = fix_migration_paths(page)['target']
        path = os.path.join(conf.paths.projectroot, conf.paths.source)

        t = libgiza.task.Task(job=verbose_remove,
                              args=[path],
                              target=True,
                              dependency=path,
                              description='removing migrated file: ' + path)
        t.append(tasks)

    logger.debog('clean: added tasks to remove {0} files'.format(len(tasks)))
    return tasks


def build_migration_task(target, source):
    return libgiza.task.Task(job=copy_if_needed,
                             args=(source, target, 'primer'),
                             target=target,
                             dependency=source)

def build_append_task(page, target, spec_files):
    return libgiza.task.Task(job=append_to_file,
                             args=(target, page['append']),
                             target=page['target'],
                             dependency=spec_files)


def build_truncate_task(truncate_spec, target, deps):
    job_args = {
        'fn': target,
        'start_after': truncate_spec['start-after'] if 'start-after' in truncate_spec else None,
        'end_before': truncate_spec['end-before'] if 'end-before' in truncate_spec else None
    }

    return libgiza.task.Task(job=truncate_file,
                             args=job_args,
                             target=target,
                             dependency=deps)
