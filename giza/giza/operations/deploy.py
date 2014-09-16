import logging
import argh

logger = logging.getLogger('giza.operations.deploy')

from giza.config.helper import fetch_config
from giza.core.app import BuildApp
from giza.deploy import Deploy
from giza.operations.sphinx import sphinx_publication
from giza.tools.command import verbose_command
from giza.tools.serialization import ingest_yaml_list, dict_from_list

@argh.arg('--target', '-t', nargs='*', dest='push_targets')
@argh.arg('--dry-run', '-d', action='store_true', dest='dry_run')
@argh.named('deploy')
def main(args):
    c = fetch_config(args)
    app = BuildApp(c)

    deploy_worker(c, app)

@argh.arg('--deploy', '-d', nargs='*', dest='push_targets')
@argh.arg('--edition', '-e', nargs='*', dest='editions_to_build')
@argh.arg('--language', '-l', nargs='*',dest='languages_to_build')
@argh.arg('--builder', '-b', nargs='*', default='html')
@argh.arg('--serial_sphinx', action='store_true', default=False)
@argh.named('push')
def publish_and_deploy(args):
    c = fetch_config(args)
    app = BuildApp(c)

    sphinx_ret = sphinx_publication(c, args, app)
    if sphinx_ret == 0 or c.runstate.force is True:
        deploy_worker(c, app)
    else:
        logger.warning(sphinx_ret + ' sphinx build(s) failed, and build not forced. not deploying.')

def deploy_worker(c, app):
    pconf = c.system.files.data.push
    pconf = dict_from_list('target', pconf)

    cmds = []
    for target in c.runstate.push_targets:
        d = Deploy(c)

        target_pconf = pconf[target]

        if target_pconf['env'] == 'publication':
            target_pconf['env'] = 'production'

        d.load(target_pconf)

        map_task = app.add('map')
        map_task.iter = d.deploy_commands()

        map_task.job = verbose_command

        cmds.extend(d.deploy_commands())

    if c.runstate.dry_run is True:
        for i in cmds:
            logger.info('dry run: {0}'.format(' '.join(i)))
    else:
        app.run()

    logger.info('completed deploy for: {0}'.format(' '.join(c.runstate.push_targets)))
