import logging
import os.path

logger = logging.getLogger(os.path.basename(__file__))
logging.basicConfig(level=logging.INFO) # set basic default log level

import argh

from app import BuildApp
from configuration import Configuration

@argh.arg('--confp')
def test(arg):
    c = Configuration(arg.confp)

    print(dir(Configuration))
    print(dir(c))
    print('---')
    print(c)


def main():
    parser = argh.ArghParser()
    parser.add_argument('--level', choices=['debug', 'warning'])

    argh.add_commands(parser, [test])

    argh.dispatch(parser)

if __name__ == '__main__':
    main()
