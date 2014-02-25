import os.path

from fabfile.utils.sphinx.config import compute_sphinx_config, get_sconf
from fabfile.utils.sphinx.workers import build_prerequisites as sphinx_prereq
from fabfile.utils.sphinx.workers import build_worker as sphinx_build

from fabfile.utils.config import lazy_conf
from fabfile.utils.shell import command
from fabfile.utils.project import edition_setup
from fabric.api import task

@task
def update():
    "Builds gettext and updates 'locale/' directory with new files."

    sphinx_builder = 'gettext'

    conf = lazy_conf(None)
    sconf = compute_sphinx_config(sphinx_builder, get_sconf(conf), conf)
    conf = edition_setup(sconf.edition, conf)

    sphinx_prereq(conf)

    try:
        rm_path = os.path.join(conf.paths.projectroot,
                               conf.paths.branch_source,
                               'meta', 'includes.txt')
        os.remove(rm_path)
        print('[tx]: removed {0}'.format(rm_path))
    except OSError:
        pass

    sphinx_build(builder=sphinx_builder, conf=conf, sconf=sconf, finalize_fun=None)

    print('[tx] [sphinx]: rebuild gettext targets')

    tx_cmd = "sphinx-intl update-txconfig-resources --pot-dir {path} --transifex-project-name={name}"


    command(tx_cmd.format(path=os.path.join(conf.paths.branch_output, sphinx_builder),
                        name='-'.join(conf.project.title.lower().split())))

    print('[tx] [sphinx-intl]: updated pot directory')

@task
def push():
    "Runs 'tx push' command."
    command('tx push -s -t')
