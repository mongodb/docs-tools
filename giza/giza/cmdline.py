import json
import logging
import os

logger = logging.getLogger(os.path.basename(__file__))

import argh

from giza.config.runtime import RuntimeStateConfig

from giza.operations.configuration import render_config
from giza.operations.clean import clean

def main():
    commands = [
        render_config,
        clean
    ]

    parser = argh.ArghParser()
    parser.add_argument('--level', '-l',
                        choices=['debug', 'warning', 'info', 'critical', 'error'],
                        default='info')
    parser.add_argument('--serial', '-s', default=None, dest='runner', const='serial', action='store_const')
    parser.add_argument('--force', '-f', default=False, action='store_true')

    argh.add_commands(parser, commands)

    args = RuntimeStateConfig()
    argh.dispatch(parser, namespace=args)

if __name__ == '__main__':
    main()
