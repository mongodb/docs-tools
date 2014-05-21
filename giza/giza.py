import logging
import os.path
import json

logger = logging.getLogger(os.path.basename(__file__))

import argh

from app import BuildApp
from config.main import Configuration
from config.runtime import RuntimeStateConfig

@argh.arg('--conf_path', '-c')
@argh.arg('--edition', '-e')
@argh.arg('--language', '-l')
def test(args):
    c = Configuration()
    c.ingest(args.conf_path)
    c.runstate = args

    dynamics = [ c.git.commit, c.paths.public, c.git.branches.current, c.git.branches.manual,
                 c.git.branches.published, c.paths.branch_output, c.paths.buildarchive,
                 c.paths.branch_source, c.paths.branch_staging, c.version.published,
                 c.version.stable, c.version.upcoming, c.project.edition, c.deploy,
                 c.paths.global_config ]


    print('--- ' + "str of object >>>")
    print(json.dumps(c.dict(), indent=3))
    print('---  >>>')

def main():
    parser = argh.ArghParser()
    parser.add_argument('--level', '-l',
                        choices=['debug', 'warning', 'info', 'critical', 'error'],
                        default='info')

    argh.add_commands(parser, [test])

    args = RuntimeStateConfig()
    argh.dispatch(parser, namespace=args)

if __name__ == '__main__':
    main()
