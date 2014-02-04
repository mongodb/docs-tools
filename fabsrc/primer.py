import os.path

from fabfile.utils.config import lazy_conf
from fabfile.utils.serialization import ingest_yaml_list
from fabfile.utils.files import copy_if_needed, copy_always
from fabfile.utils.transformations import post_process_jobs, truncate_file, append_to_file
from fabfile.utils.errors import FileNotFoundError

from fabfile.make import runner

from fabric.api import task

def migrate_pages(conf=None):
    conf = lazy_conf(conf)

    migration_path = os.path.join(conf.paths.projectroot,
                                  conf.paths.builddata,
                                  'primer_migrations.yaml')
    if conf.project.name != 'primer':
        return None
    elif not os.path.exists(migration_path):
        return None
    else:
        migrations = ingest_yaml_list(migration_path)

        truncate_jobs = []
        munge_jobs = []
        migration_jobs = []
        append_jobs = []
        for page in migrations:
            page = fix_abs_paths(page)

            fq_target = os.path.join(conf.paths.projectroot,
                                     conf.paths.source,
                                     page['target'])

            fq_source = os.path.join(conf.paths.manual_source,
                                     page['source'])

            if not os.path.exists(fq_source):
                raise FileNotFoundError("[primer-migration]: source file {0} doesn't exist".format(fq_source))

            if fq_target.endswith('.txt'):
                print('[primer-migration] [warning]: ({0}) imported files cannot end with ".txt", changing to ".rst"'.format(page['source']))
                fq_target = fq_target.replace('.txt', '.rst')

            migration_jobs.append({
                'target': fq_target,
                'dependency': None,
                'job': copy_if_needed,
                'args': [ fq_source, fq_target, 'primer-migration' ]
            })

            if 'truncate' in page:
                t = page['truncate']
                truncate_jobs.append({
                    'target': fq_target,
                    'depdendecy': None,
                    'job': truncate_file,
                    'args': {
                        'fn': fq_target,
                        'start_after': t['start-after'] if 'start-after' in t else None,
                        'end_before': t['end-before'] if 'end-before' in t else None},
                })

            if 'transform' in page:
                migration_jobs[-1]['job'] = copy_always

                munge_jobs.append({
                    'file': fq_target,
                    'type': 'primer-migration-processing',
                    'transform': page['transform']
                })

            if 'append' in page:
                append_jobs.append({
                    'job': append_to_file,
                    'target': page['target'],
                    'dependency': migration_path,
                    'args': [ fq_target, page['append']]
                })

        migration_res = runner(migration_jobs)

        if len(munge_jobs) != 0:
            munge_res = runner(post_process_jobs(tasks=munge_jobs))
        else:
            munge_res = list()

        if len(truncate_jobs) != 0:
            truncate_res = runner(truncate_jobs)
        else:
            truncate_res = list()

        if len(append_jobs) != 0:
            append_res = runner(append_jobs)
        else:
            append_res = list()

        msg = '[primer-migration]: migrated {0}, munged {1}, truncated {2}, and appended to {3} pages.'
        print(msg.format(len(migration_res), len(munge_res), len(truncate_res), len(append_res)))

        return True

def fix_abs_paths(page):
    if 'target' not in page:
        page['target'] = page['source']

    for field  in ['source', 'target']:
        if page[field].startswith('/'):
            page[field] = page[field][1:]

    return page
