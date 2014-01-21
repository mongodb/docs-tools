import os
import itertools

from fabfile.utils.config import lazy_conf
from fabfile.utils.jobs.dependency import dump_file_hashes
from fabfile.utils.jobs.errors import PoolResultsError
from fabfile.utils.output import build_platform_notification
from fabfile.utils.shell import command

from fabfile.intersphinx import intersphinx_jobs
from fabfile.make import runner

import fabfile.generate as generate
import fabfile.process as process

def build_prereq_jobs(conf):
    jobs = [
        {
            'job': generate.robots_txt_builder,
            'args': [ os.path.join( conf.paths.projectroot,
                                    conf.paths.public,
                                    'robots.txt'),
                      conf
                    ]
        },
        {
            'job': generate.write_include_index,
            'args': [conf]
        }
    ]

    for job in jobs:
        yield job

def build_prerequisites(conf):
    jobs = itertools.chain(process.manpage_jobs(conf),
                           build_prereq_jobs(conf),
                           generate.table_jobs(conf),
                           generate.api_jobs(conf),
                           generate.toc_jobs(conf),
                           generate.option_jobs(conf),
                           generate.steps_jobs(conf),
                           generate.release_jobs(conf),
                           intersphinx_jobs(conf),
                           generate.image_jobs(conf)
        )

    try:
        res = runner(jobs)
        print('[sphinx-prep]: built {0} pieces of content'.format(len(res)))
    except PoolResultsError:
        print('[WARNING]: sphinx prerequisites encountered errors. '
              'See output above. Continuing as a temporary measure.')

    generate.buildinfo_hash(conf)
    if conf.project.name != 'mms':
        # we copy source manually for mms in makefile.mms, avoiding this
        # operation to clarify the artifacts directory
        generate.source(conf)

    print('[sphinx-prep]: resolving all intra-source dependencies now. (takes several seconds)')
    dep_count = process.refresh_dependencies(conf)
    print('[sphinx-prep]: bumped timestamps of {0} files'.format(dep_count))

    command(build_platform_notification('Sphinx', 'Build in progress past critical phase.'))

    print('[sphinx-prep]: INFO - Build in progress past critical phase.')

    dump_file_hashes(conf.system.dependency_cache, conf)
    print('[sphinx-prep]: build environment prepared for sphinx.')
