import logging
import os.path

logger = logging.getLogger(os.path.basename(__file__))

from fabfile.utils.sphinx.config import get_sconf
from fabfile.utils.sphinx.workers import build_worker as sphinx_build
from fabfile.utils.structures import StateAttributeDict

from fabfile.utils.config import lazy_conf
from fabfile.utils.shell import command
from fabfile.utils.project import edition_setup
from fabfile.make import runner
from fabric.api import task

@task
def update():
    "Builds gettext and updates 'locale/' directory with new files."

    sphinx_builder = 'gettext'

    conf = lazy_conf(None)
    sconf = get_sconf(conf)
    sconf.builder = sphinx_builder
    sync = StateAttributeDict()

    if 'edition' in sconf:
        conf = edition_setup(sconf.edition, conf)

    # includes_file = os.path.join(conf.paths.branch_source, 'meta', 'includes.txt')
    # if os.path.exists(includes_file):
    #     os.remove(includes_file)

    sphinx_build(builder=sphinx_builder, conf=conf, sconf=sconf, sync=sync, finalize_fun=None)
    logger.info('rebuilt gettext targets')

    tx_cmd = "sphinx-intl update-txconfig-resources --pot-dir {path} --transifex-project-name={name}"

    logger.info('updating translation artifacts. Long running.')
    r = command(tx_cmd.format(path=os.path.join(conf.paths.branch_output, sphinx_builder),
                              name='-'.join(conf.project.title.lower().split())),
                capture=True, ignore=True)


    if r.return_code != 0:
        logger.critical('uploading translations failed.')
        logger.warning(r.err)
        raise SystemExit
    else:
        logger.info(r.out)
        logger.info('sphinx_intl completed successfully: translation uploaded.')

    logger.info('sphinx-intl: updated pot directory')
    check()
    logger.info('completed translation file check.')


def tx_resources():
    conf = lazy_conf(None)
    tx_conf = os.path.join(conf.paths.projectroot,
                           ".tx", 'config')

    with open(tx_conf, 'r') as f:
        resources = [ l.strip()[1:-1]
                      for l in f.readlines()
                      if l.startswith('[')][1:]

    return resources

def logged_command(verb, cmd):
    r = command(cmd, capture=True)
    logger.info('{0}ed {1}'.format(verb, cmd.split(' ')[-1]))

    return r.out

@task
def pull(lang):
    "Runs 'tx pull' command."

    resources = tx_resources()

    jobs = [ { 'job': logged_command,
               'args': [ 'pull', ' '.join([ 'tx', 'pull', '-l', lang, '-r', page]) ] }
             for page in resources ]

    runner(jobs, parallel='thread', pool=12)

@task
def push():
    "Runs 'tx push' command."
    resources = tx_resources()

    jobs = [ { 'job': logged_command,
               'args': ['push', ' '.join([ 'tx', 'push', '-s', '-r', page]) ] }
             for page in resources ]

    runner(jobs, parallel='thread', pool=12)

@task
def check():
    conf = lazy_conf(None)

    tx_conf = os.path.join(conf.paths.projectroot,
                           ".tx", 'config')

    with open(tx_conf, 'r') as f:
        files = [ l.rsplit(' ', 1)[1].strip()
                  for l in f.readlines()
                  if l.startswith('source_file')]

    errs = 0
    for fn in files:
        fqfn = os.path.join(conf.paths.projectroot, fn)

        if not os.path.exists(fn):
            errs += 1
            logger.error(fn + " does not exist.")

    if errs != 0:
        logger.warning("{0} files configured that don't exist.")
    else:
        logger.info('all configured translation source files exist')

    return errs
