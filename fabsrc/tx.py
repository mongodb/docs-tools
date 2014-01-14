import os.path

from sphinx import compute_sphinx_config, edition_setup
from sphinx import build_prerequisites as sphinx_prereq
from sphinx import build_worker as sphinx_build

from fabric.api import task, local
from docs_meta import get_conf

@task
def update():
    "Builds gettext and updates 'locale/' directory with new files."

    sphinx_builder = 'gettext'

    conf = get_conf()
    sconf = compute_sphinx_config(sphinx_builder, conf)
    conf = edition_setup(sconf.edition, conf)

    sphinx_prereq(conf)
    sphinx_build(builder=sphinx_builder, root=conf.paths.branch_output, tag=None, conf=conf)

    print('[tx] [sphinx]: rebuild gettext targets')

    tx_cmd = "sphinx-intl update-txconfig-resources --pot-dir {path} --transifex-project-name={name}"

    local(tx_cmd.format(path=os.path.join(conf.paths.branch_output, sphinx_builder),
                        name='-'.join(conf.project.title.lower().split())))

    print('[tx] [sphinx-intl]: updated pot directory')

@task
def push():
    "Runs 'tx push' command."
    local('tx push -s -t')
