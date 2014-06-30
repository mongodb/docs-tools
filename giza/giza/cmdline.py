import json
import logging

logger = logging.getLogger('giza.main')

import argh

from giza.config.runtime import RuntimeStateConfig

import giza.operations.generate
import giza.operations.includes
from giza.operations.configuration import render_config
from giza.operations.clean import clean
from giza.operations.git import apply_patch, pull_rebase, cherry_pick
from giza.operations.sphinx import sphinx
from giza.operations.deploy import push

def main():
    parser = argh.ArghParser()
    parser.add_argument('--level', '-l',
                        choices=['debug', 'warning', 'info', 'critical', 'error'],
                        default='info')
    parser.add_argument('--serial', '-s', default=None, dest='runner', const='serial', action='store_const')
    parser.add_argument('--force', '-f', default=False, action='store_true')

    commands = [
        render_config,
        clean,
        sphinx,
        push
    ]

    argh.add_commands(parser, commands)
    argh.add_commands(parser, [apply_patch, pull_rebase, cherry_pick], namespace='git')

    generate_commands = [
        giza.operations.generate.api,
        giza.operations.generate.assets,
        giza.operations.generate.images,
        giza.operations.generate.intersphinx,
        giza.operations.generate.options,
        giza.operations.generate.primer,
        giza.operations.generate.steps,
        giza.operations.generate.tables,
        giza.operations.generate.toc,
    ]

    argh.add_commands(parser, generate_commands, namespace='generate')

    include_commands = [
        giza.operations.includes.recursive,
        giza.operations.includes.changed,
        giza.operations.includes.once,
        giza.operations.includes.unused,
        giza.operations.includes.list,
        giza.operations.includes.graph,
        giza.operations.includes.clean,
    ]

    argh.add_commands(parser, include_commands, namespace='includes')

    args = RuntimeStateConfig()
    argh.dispatch(parser, namespace=args)

if __name__ == '__main__':
    main()
