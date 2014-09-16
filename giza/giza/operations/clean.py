import os
import logging

logger = logging.getLogger('giza.operations.clean')

import argh

from giza.core.app import BuildApp
from giza.config.main import Configuration
from giza.tools.files import rm_rf

@argh.arg('--conf_path', '-c')
@argh.arg('--builder', '-b', dest='builder_to_delete')
@argh.arg('--length', default=None, type=int, dest='days_to_save')
@argh.named('clean')
def main(args):
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
        m = 'removing artifact: {0}'.format(fn)
        t.description = m
        logger.critical(m)

    app.run()
