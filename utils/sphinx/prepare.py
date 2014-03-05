import os
import itertools

from threading import Lock

from fabfile.intersphinx import intersphinx_jobs
from fabfile.primer import primer_migrate_pages
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
from utils.sphinx.config import get_sconf

mms_makefile_lock = Lock()

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
           },
           {
               'job': primer_migrate_pages,
               'args': [conf]
           }
        ])
    else:
        raise StopIteration

    for job in jobs:
        yield job

def build_process_prerequsites(conf):
    jobs = itertools.chain(build_prereq_jobs(conf),
                           manpage_jobs(conf),
                           table_jobs(conf),
                           api_jobs(conf),
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

    buildinfo_hash(conf)

def build_job_prerequsites(conf, sconf):
    jobs = toc_jobs(conf)

    try: 
        res = runner(jobs, parallel='process')
        print('[sphinx-prep]: built {0} pieces of content'.format(len(res)))
    except PoolResultsError:
        print('[WARNING]: sphinx prerequisites encountered errors. '
              'See output above. Continuing as a temporary measure.')

    runner(external_jobs(conf), parallel='thread')

    if conf.project.name == 'mms':
        cmd = 'make -C {0} {1}-source-dir={0}{2}{3}-{4} EDITION={1} generate-source-{1}'
        cmd = cmd.format(conf.paths.projectroot, sconf.edition, os.path.sep,
                         conf.paths.branch_source, sconf.builder)
        with mms_makefile_lock:
            o = command(cmd, capture=True)
        if len(o.out.strip()) > 0:
            print(o.out)
    else:
        transfer_source(sconf, conf)

    print('[sphinx-prep]: resolving all intra-source dependencies now. (takes several seconds)')
    dep_count = refresh_dependencies(conf)
    print('[sphinx-prep]: bumped timestamps of {0} files'.format(dep_count))

    command(build_platform_notification('Sphinx', 'Build in progress pastb critical phase.'), ignore=True)

    print('[sphinx-prep]: INFO - Build in progress past critical phase for {0} build'.format(sconf.builder))

    dump_file_hashes(conf)
    print('[sphinx-prep]: build environment prepared for sphinx.')

def build_prerequisites(conf):
    build_process_prerequsites(conf)
    build_job_prerequsites(conf, get_sconf(conf))
