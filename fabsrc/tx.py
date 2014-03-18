import os.path

from fabfile.utils.sphinx.config import get_sconf
from fabfile.utils.sphinx.workers import build_worker as sphinx_build
from fabfile.utils.structures import StateAttributeDict

from fabfile.utils.config import lazy_conf
from fabfile.utils.shell import command
from fabfile.utils.project import edition_setup
from fabric.api import task

@task
def update():
    "Builds gettext and updates 'locale/' directory with new files."

    sphinx_builder = 'gettext'

    conf = lazy_conf(None)
    sconf = get_sconf(conf)

    sconf.builder = sphinx_builder

    if 'edition' in sconf:
        conf = edition_setup(sconf.edition, conf)

    sync = StateAttributeDict()

    sphinx_build(builder=sphinx_builder, conf=conf, sconf=sconf, sync=sync, finalize_fun=None)

    print('[tx] [sphinx]: rebuild gettext targets')

    tx_cmd = "sphinx-intl update-txconfig-resources --pot-dir {path} --transifex-project-name={name}"

    command(tx_cmd.format(path=os.path.join(conf.paths.branch_output, sphinx_builder),
                        name='-'.join(conf.project.title.lower().split())))

    print('[tx] [sphinx-intl]: updated pot directory')

@task
def push():
    "Runs 'tx push' command."
    command('tx push -s -t')
