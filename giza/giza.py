import logging
import os.path
import json

logger = logging.getLogger(os.path.basename(__file__))
logging.basicConfig(level=logging.INFO) # set basic default log level

import argh

from app import BuildApp
from configuration import Configuration, RuntimeStateConfiguration

@argh.arg('--confp')
def test(arg):
    c = Configuration()
    c.ingest(arg.confp)
    r = RuntimeStateConfiguration()
    c.runstate = r

    print(hasattr(c, 'project'))
    dynamics = [ c.git.commit, c.paths.public, c.git.branches.current, c.git.branches.manual,
                 c.git.branches.published, c.paths.branch_output, c.paths.buildarchive,
                 c.paths.branch_source, c.paths.branch_staging, c.version.published,
                 c.version.stable, c.version.upcoming,
                 c.paths.global_config ]

    print(dynamics)


    # print('--- ' + "dir of rendered object >>>")
    # print(dir(c))
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
