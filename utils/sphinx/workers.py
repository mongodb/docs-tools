import os.path

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
                'args': [ target, lsconf, lconf, sync, finalize_fun]
            })
        else:
            print('[sphinx] [warning]: not building {0} without configuration.'.format(target))

    # a batch of prereq jobs go here.
    primer_migrate_pages(conf)
    build_process_prerequsites(conf)
    
    if len(target_jobs) <= 1:
        res = runner(target_jobs, pool=1)
    else:
        res = runner(target_jobs, parallel='threads')

    output_sphinx_stream('\n'.join([r for r in res if r is not None]), conf)

    print('[sphinx]: build {0} sphinx targets'.format(len(res)))

def build_worker(builder, sconf, conf, sync, finalize_fun):
    dirpath = os.path.join(conf.paths.branch_output, builder)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
        print('[{0}]: created {1}'.format(builder, dirpath))

    # a batch of prereq jobs go here. (if they need the modified conf.)
    build_job_prerequsites(sync, sconf, conf)

    print('[{0}]: starting {0} build {1}'.format(builder, timestamp()))

    cmd = 'sphinx-build {0} -d {1}/doctrees-{2} {3} {4}' # per-builder-doctreea
    sphinx_cmd = cmd.format(get_sphinx_args(sconf, conf),
                            os.path.join(conf.paths.projectroot, conf.paths.branch_output),
                            builder,
                            os.path.join(conf.paths.projectroot, conf.paths.branch_source), 
                            os.path.join(conf.paths.projectroot, conf.paths.branch_output, builder))

    out = command(sphinx_cmd, capture=True, ignore=True)
    # out = sphinx_native_worker(sphinx_cmd)
    print('[build]: completed {0} build at {1}'.format(builder, timestamp()))

    output = '\n'.join([out.err, out.out])

    if out.return_code == 0:
        print('[sphinx]: successfully completed {0} build at {1}!'.format(builder, timestamp()))
        if finalize_fun is not None:
            finalize_fun(builder, sconf, conf)
            print('[sphinx]: finalized {0} build at {1}'.format(builder, timestamp()))
        return output
    else:
        print('[sphinx]: the {0} build was not successful. not running finalize steps'.format(builder))
        output_sphinx_stream(output, conf)
        return None
