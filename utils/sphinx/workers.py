import os.path
import logging

logger = logging.getLogger(os.path.basename(__file__))

from fabfile.utils.project import edition_setup
from fabfile.utils.strings import timestamp
from fabfile.utils.shell import command

from fabfile.make import runner

from fabfile.primer import primer_migrate_pages

from utils.structures import StateAttributeDict

from fabfile.utils.sphinx.prepare import build_job_prerequsites, build_process_prerequsites
from fabfile.utils.sphinx.output import output_sphinx_stream
from fabfile.utils.sphinx.config import compute_sphinx_config, get_sphinx_args, get_sconf

def sphinx_build(targets, conf, sconf, finalize_fun):
    if len(targets) == 0:
        targets.append('html')

    target_jobs = []

    sync = StateAttributeDict()
    for target in targets:
        if target in sconf:
            lsconf = compute_sphinx_config(target, sconf, conf)
            lconf = edition_setup(lsconf.edition, conf)

            target_jobs.append({
                'job': build_worker,
                'args': [ target, lsconf, lconf, sync, finalize_fun],
                'description': "sphinx build worker for {0}".format(target)
            })
        else:
            logger.warning('not building sphinx target {0} without configuration.'.format(target))

    # a batch of prereq jobs go here.
    primer_migrate_pages(conf)
    build_process_prerequsites(sync, conf)

    res = runner(target_jobs, parallel='threads')

    output_sphinx_stream('\n'.join([r[1] if isinstance(r, tuple) else r
                                    for r in res
                                    if r is not None]), conf)

    logger.info('build {0} sphinx targets'.format(len(res)))

def build_worker(builder, sconf, conf, sync, finalize_fun):
    dirpath = os.path.join(conf.paths.branch_output, builder)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
        logger.info('created directories "{1}" for sphinx builder {0}'.format(builder, dirpath))

    # a batch of prereq jobs go here. (if they need the modified conf.)
    build_job_prerequsites(sync, sconf, conf)

    logger.info('starting sphinx build {0} at {1}'.format(builder, timestamp()))

    cmd = 'sphinx-build {0} -d {1}/doctrees-{2} {3} {4}' # per-builder-doctreea

    sphinx_cmd = cmd.format(get_sphinx_args(sconf, conf),
                            os.path.join(conf.paths.projectroot, conf.paths.branch_output),
                            builder,
                            os.path.join(conf.paths.projectroot, conf.paths.branch_source),
                            os.path.join(conf.paths.projectroot, conf.paths.branch_output, builder))

    out = command(sphinx_cmd, capture=True, ignore=True)
    # out = sphinx_native_worker(sphinx_cmd)
    logger.info('completed sphinx build {0} at {1}'.format(builder, timestamp()))

    output = '\n'.join([out.err, out.out])

    if out.return_code == 0:
        logger.info('successfully completed {0} sphinx build at {1}!'.format(builder, timestamp()))
        if finalize_fun is not None:
            finalize_fun(builder, sconf, conf)
            logger.info('finalized sphinx {0} build at {1}'.format(builder, timestamp()))
        return output
    else:
        logger.warning('the sphinx build {0} was not successful. not running finalize steps'.format(builder))
        output_sphinx_stream(output, conf)
        return None
