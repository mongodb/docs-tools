import os.path

from utils.config import lazy_conf
from utils.serialization import ingest_yaml_list
from utils.files import copy_if_needed
from utils.transformations import post_process_jobs

from make import runner

def migrate_pages(conf=None):
    conf = lazy_conf(conf)

    migration_path = os.path.join(conf.paths.project_root,
                                  conf.paths.builddata,
                                  'primer_migrations.yaml')
    if conf.project.name != 'primer':
        return None
    elif not os.path.exists(migration_path)
        return None
    else:
        migrations = ingest_yaml_list(migration_path)

        munge_jobs = []
        migration_jobs = []
        for page in migrations:
            fq_target = os.path.join(conf.paths.projectroot, conf.paths.source, page['target'])
            migration_jobs.append({
                'target': page['target']
                'dependency': None,
                'job': copy_if_needed,
                'args': [ os.path.join(conf.paths.manual_source, page['source']),
                          fq_target,
                          'primer-migration'
                        ]
            })

            if 'transform' in page:
                munge_jobs.append({
                    'file': fq_target,
                    'type': 'primer-migration-processing'
                    'transform': page['transformation']
                })

        migration_res = runner(migration_jobs)

        if len(munge_jobs) != 0:
            munge_res = runner(munge_jobs)
        else:
            munge_res = list()

        msg = '[primer]: migrated {0} pages and munged {1} pages.'
        print(msg.format(len(migration_res), len(munge_res)))

        return True
