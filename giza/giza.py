import logging
import os.path

logger = logging.getLogger(os.path.basename(__file__))

import argh

from app import BuildApp
from configuration import Configuration

def test(arg):
    print arg

def main():
    parser = argh.ArghParser()
    parser.add_argument('--level', choices=['debug', 'warning'])

    argh.add_commands(parser, [test])

    argh.dispatch(parser)

if __name__ == '__main__':
    main()
