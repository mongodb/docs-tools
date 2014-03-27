import os

from fabfile.utils.config import lazy_conf
from fabfile.utils.serialization import ingest_yaml_list
from fabfile.utils.files import copy_if_needed, copy_always, expand_tree
from fabfile.utils.transformations import post_process_jobs, truncate_file, append_to_file
from fabfile.utils.errors import FileNotFoundError
from fabfile.utils.jobs.context_pools import ProcessPool

from fabric.api import task

def get_migration_specifications(conf):
    return [ fn for fn in expand_tree(os.path.join(conf.paths.projectroot,
                                                   conf.paths.builddata))
             if 'primer' in fn and 'migrations' in fn ]

def convert_multi_source(page):
    return [ { 'source': source } for source in page['sources'] ]

@task
def clean(conf=None):
    "Removes all migrated primer files according to the current spec."

    conf = lazy_conf(conf)

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

def verbose_remove(path):
    if os.path.exists(path):
        logger.debug('clean: removing {0}'.format(path))
        os.remove(path)

@task
def migrate():
    primer_migrate_pages()

def primer_migrate_pages(conf=None):
    "Migrates all manual files to primer according to the spec. As needed."

    conf = lazy_conf(conf)

    migration_paths = get_migration_specifications(conf)

    if conf.project.name != 'primer':
        return False
    elif len(migration_paths) == 0:
        return False
    else:
        migrations = ingest_yaml_list(*migration_paths)

        truncate_jobs = []
        munge_jobs = []
        migration_jobs = []
        append_jobs = []

        for page in migrations:
            if 'sources' in page:
                migrations.extend(convert_multi_source(page))
                continue

            page = fix_migration_paths(page)

            fq_target = os.path.join(conf.paths.projectroot, conf.paths.source, page['target'])
            fq_source = os.path.join(conf.paths.manual_source, page['source'])

            migration_jobs.append(build_migration_job(fq_target, fq_source))

            if 'truncate' in page:
                truncate_jobs.append(build_truncate_job(page['truncate'], fq_target))

            if 'transform' in page:
                migration_jobs[-1]['job'] = copy_always
                munge_jobs.append(build_transform_job(page['transform'], fq_target))

            if 'append' in page:
                migration_jobs[-1]['job'] = copy_always
                append_jobs.append(build_append_job(page, fq_target, migration_paths))

        with ProcessPool() as p:
            migration_res = p.runner(migration_jobs)
            munge_res = p.runner(post_process_jobs(tasks=munge_jobs))
            truncate_res = p.runner(truncate_jobs)
            append_res = p.runner(append_jobs)

        msg = 'migrated {0}, munged {1}, truncated {2}, and appended to {3} pages.'
        logger.info(msg.format(len(migration_res), len(munge_res), len(truncate_res), len(append_res)))

        return True

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

def build_migration_job(target, source):
    return {
        'target': target,
        'job': copy_if_needed,
        'args': [ source, target, 'primer' ]
    }

def build_transform_job(transform, target):
    return {
        'file': target,
        'type': 'primer-processing',
        'transform': transform
    }

def build_append_job(page, target, spec_files):
    return {
        'job': append_to_file,
        'target': page['target'],
        'dependency': spec_files,
        'args': [ target, page['append']]
    }

def build_truncate_job(truncate_spec, target):
    return {
        'target': target,
        'job': truncate_file,
        'args': {
            'fn': target,
            'start_after': truncate_spec['start-after'] if 'start-after' in truncate_spec else None,
            'end_before': truncate_spec['end-before'] if 'end-before' in truncate_spec else None},
    }
