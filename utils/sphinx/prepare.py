import os
import itertools
import logging

logger = logging.getLogger(os.path.basename(__file__))

from threading import Lock
from shutil import rmtree

from fabfile.intersphinx import intersphinx_jobs
from fabfile.primer import primer_migrate_pages
from fabfile.make import runner
from fabfile.tools import Timer

from utils.jobs.dependency import dump_file_hashes
from utils.jobs.errors import PoolResultsError
from utils.jobs.context_pools import ProcessPool
from utils.output import build_platform_notification
from utils.shell import command
from utils.structures import StateAttributeDict

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

update_source_lock = Lock()

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
                           release_jobs(conf),
                           intersphinx_jobs(conf))

    image_res = runner(image_jobs(conf), parallel='process')
    logger.info('build {0} images and associated files'.format(len(image_res)))

    try:
        res = runner(jobs, parallel='process')
        logger.info('built {0} pieces of content to prep for sphinx build'.format(len(res)))
    except PoolResultsError:
        logger.error('sphinx prerequisites encountered errors. '
                     'See output. Continuing as a temporary measure.')

    buildinfo_hash(conf)

def build_job_prerequsites(sync, sconf, conf):
    runner(external_jobs(conf), parallel='thread')

    with update_source_lock:
        cond_toc = "build_toc"
        cond_name = 'transfered_source'
        cond_dep = 'updated_deps'
        cond_steps = 'build_step_files'

        if conf.project.name == 'mms':
            cond_name += '_' + sconf.edition
            cond_toc += '_' + sconf.edition
            cond_dep += '_' + sconf.edition
            cond_steps += '_' + sconf.edition

        if sync.satisfied(cond_name) is False:
            transfer_source(sconf, conf)
            sync[cond_name] = True

        if 'excluded' in sconf:
            logger.info('removing excluded files')
            for fn in sconf.excluded:
                fqfn = os.path.join(conf.paths.projectroot, conf.paths.branch_source, fn[1:])
                if os.path.exists(fqfn):
                    if os.path.isdir(fqfn):
                        rmtree(fqfn)
                    else:
                        os.remove(fqfn)
                    logger.info('removed {0}'.format(fqfn))

        with ProcessPool() as p:
            # these must run here so that MMS can generate different toc/steps/etc for
            # each edition.

            if sync.satisfied(cond_toc) is False:
                # even if this fails we don't want it to run more than once
                sync[cond_toc] = True
                tr = p.runner(toc_jobs(conf))
                logger.info('generated {0} toc files'.format(len(tr)))

            if sync.satisfied(cond_steps) is False:
                sync[cond_steps] = True
                sr = p.runner(steps_jobs(conf))
                logger.info('generated {0} step files'.format(len(sr)))

        if sync.satisfied(cond_dep) is False:
            logger.debug('using update deps lock.')

            logger.info('resolving all intra-source dependencies now. for sphinx build. (takes several seconds)')
            dep_count = refresh_dependencies(conf)
            logger.info('bumped {0} dependencies'.format(dep_count))
            sync[cond_dep] = True

            command(build_platform_notification('Sphinx', 'Build in progress past critical phase.'), ignore=True)
            logger.info('sphinx build in progress past critical phase ({0})'.format(conf.paths.branch_source))
            dump_file_hashes(conf)
        else:
            logger.debug('dependencies already updated, lock unneeded.')

        logger.debug('releasing dependency update lock.')

    logging.info('build environment prepared for sphinx build {0}.'.format(sconf.builder))

def build_prerequisites(conf):
    sync = StateAttributeDict()
    build_process_prerequsites(conf)
    build_job_prerequsites(sync, get_sconf(conf), conf)
