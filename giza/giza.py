import json
import logging
import os

logger = logging.getLogger(os.path.basename(__file__))

import argh

from app import BuildApp
from config.main import Configuration
from config.runtime import RuntimeStateConfig

@argh.arg('--conf_path', '-c')
@argh.arg('--edition', '-e')
@argh.arg('--language', '-l')
def config(args):
    c = Configuration()
    c.ingest(args.conf_path)
    c.runstate = args

    # the following values are rendered lazily. we list them here so that the
    # final object will be useful to inspect.

    dynamics = [ c.git.commit, c.paths.public, c.git.branches.current, c.git.branches.manual,
                 c.git.branches.published, c.paths.branch_output, c.paths.buildarchive,
                 c.paths.branch_source, c.paths.branch_staging, c.version.published,
                 c.version.stable, c.version.upcoming, c.project.edition, c.deploy,
                 c.paths.global_config, c.project.branched, c.system.dependency_cache,
                 c.paths.public_site_output, c.project.basepath,
                 c.runstate.runner, c.runstate.force
               ]

    print('--- ' + "str of config object >>>")
    print(json.dumps(c.dict(), indent=3))
    print('---  >>>')

from utils.files import rm_rf

@argh.arg('--conf_path', '-c')
@argh.arg('--builder', '-b', dest='builder_to_delete')
@argh.arg('--length', default=None, type=int, dest='days_to_save')
def clean(args):
    c = Configuration()
    c.ingest(args.conf_path)
    c.runstate = args
    app = BuildApp(c)

    to_remove = []
    if c.runstate.builder_to_delete is not None:
        builder = c.runstate.builder_to_delete
        to_remove.append( os.path.join(c.paths.branch_output, 'doctrees-' + builder))
        to_remove.append( os.path.join(c.paths.branch_output, builder))
        m = 'remove artifacts associated with the {0} builder in {1}'
        logger.debug(m.format(builder, c.git.branches.current))

    if c.runstate.days_to_save is not None:
        published_branches = [ 'docs-tools', 'archive', 'public', 'primer', c.git.branches.current ]
        published_branches.extend(c.git.branches.published)

        for build in os.listdir(os.path.join(c.paths.projectroot, c.paths.output)):
            build = os.path.join(c.paths.projectroot, c.paths.output, build)
            branch = os.path.split(build)[1]

            if branch in published_branches:
                continue
            elif not os.path.isdir(build):
                continue
            elif os.stat(build).st_mtime > c.runstate.days_to_save:
                to_remove.append(build)
                to_remove.append(os.path.join(c.paths.projectroot, c.paths.output, 'public', branch))
                logger.debug('removed stale artifacts: "{0}" and "build/public/{0}"'.format(branch))

    for fn in to_remove:
        t = app.add()
        t.job = rm_rf
        t.args = fn
        logger.critical('removing artifact: {0}'.format(fn))

    app.run()

def main():
    parser = argh.ArghParser()
    parser.add_argument('--level', '-l',
                        choices=['debug', 'warning', 'info', 'critical', 'error'],
                        default='info')
    parser.add_argument('--serial', '-s', default=None, dest='runner', const='serial', action='store_const')
    parser.add_argument('--force', '-f', default=False, action='store_true')

    argh.add_commands(parser, [config, clean])

    args = RuntimeStateConfig()
    argh.dispatch(parser, namespace=args)

if __name__ == '__main__':
    main()
