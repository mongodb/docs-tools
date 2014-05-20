import logging
import os.path
import json

logger = logging.getLogger(os.path.basename(__file__))
logging.basicConfig(level=logging.INFO) # set basic default log level

import argh

from app import BuildApp
from configuration import Configuration

@argh.arg('--confp')
def test(arg):
    c = Configuration(arg.confp)

    print(c.git.commit)
    print(c.git.dict())
    print(c.git.branches.repo.current_branch())

    print(c.git.branches.current)
    print('--- ' + "dir of rendered object >>>")
    print(dir(c))
    print('--- ' + "str of object >>>")
    print(json.dumps(c.dict(), indent=3))
    print('---  >>>')


def main():
    parser = argh.ArghParser()
    parser.add_argument('--level', choices=['debug', 'warning'])

    argh.add_commands(parser, [test])

    argh.dispatch(parser)

if __name__ == '__main__':
    main()
