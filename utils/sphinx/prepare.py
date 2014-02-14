import os
import itertools

from fabfile.intersphinx import intersphinx_jobs
from fabfile.make import runner

from utils.jobs.dependency import dump_file_hashes
from utils.jobs.errors import PoolResultsError
from utils.output import build_platform_notification
from utils.shell import command

from utils.contentlib.manpage import manpage_jobs
from utils.contentlib.table import table_jobs
from utils.contentlib.param import api_jobs
from utils.contentlib.toc import toc_jobs
from utils.contentlib.options import option_jobs
from utils.contentlib.steps import steps_jobs
from utils.contentlib.release import release_jobs
from utils.contentlib.images import image_jobs
from utils.contentlib.robots import robots_txt_builder
from utils.contentlib.includes import write_include_index
from utils.contentlib.hash import buildinfo_hash
from utils.contentlib.source import transfer_source
from utils.contentlib.external import external_jobs

from utils.sphinx.dependencies import refresh_dependencies

def build_prereq_jobs(conf):
    jobs = []
    if conf.project.name not in [ "mms", "ecosystem", "primer"]:
        jobs.extend([
            {
                'job': robots_txt_builder,
                'args': [ os.path.join( conf.paths.projectroot,
                                        conf.paths.public,
                                        'robots.txt'),
                          conf
                        ]
           },
           {
               'job': write_include_index,
               'args': [conf]
           }
        ])
    else:
        raise StopIteration

    for job in jobs:
        yield job

def build_prerequisites(conf):
    jobs = itertools.chain(build_prereq_jobs(conf),
                           manpage_jobs(conf),
                           table_jobs(conf),
                           api_jobs(conf),
                           toc_jobs(conf),
                           option_jobs(conf),
                           steps_jobs(conf),
                           release_jobs(conf),
                           intersphinx_jobs(conf),
                           image_jobs(conf))

    try:
        res = runner(jobs, parallel='process')
        print('[sphinx-prep]: built {0} pieces of content'.format(len(res)))
    except PoolResultsError:
        print('[WARNING]: sphinx prerequisites encountered errors. '
              'See output above. Continuing as a temporary measure.')

    runner(external_jobs(conf), parallel='thread')

    buildinfo_hash(conf)

    if conf.project.name != 'mms':
        # we copy source manually for mms in makefile.mms, avoiding this
        # operation to clarify the artifacts directory
        transfer_source(conf)

    print('[sphinx-prep]: resolving all intra-source dependencies now. (takes several seconds)')
    dep_count = refresh_dependencies(conf)
    print('[sphinx-prep]: bumped timestamps of {0} files'.format(dep_count))

    command(build_platform_notification('Sphinx', 'Build in progress pastb critical phase.'), ignore=True)

    print('[sphinx-prep]: INFO - Build in progress past critical phase.')

    dump_file_hashes(conf.system.dependency_cache, conf)
    print('[sphinx-prep]: build environment prepared for sphinx.')
