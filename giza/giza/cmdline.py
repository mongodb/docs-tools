# Copyright 2014 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

import argh

from giza.config.runtime import RuntimeStateConfig

import giza.operations.clean
import giza.operations.configuration
import giza.operations.deploy
import giza.operations.generate
import giza.operations.git
import giza.operations.includes
import giza.operations.make
import giza.operations.packaging
import giza.operations.build_env
import giza.operations.quickstart
import giza.operations.sphinx_cmds
import giza.operations.tx
import giza.operations.code_review
import giza.operations.test
import giza.operations.changelog

logger = logging.getLogger('giza.main')

commands = {
    'main': [
        giza.operations.clean.main,
        giza.operations.configuration.render_config,
        giza.operations.deploy.main,
        giza.operations.deploy.publish_and_deploy,
        giza.operations.quickstart.make_project,
        giza.operations.sphinx_cmds.main,
        giza.operations.deploy.twofa_code,
        giza.operations.configuration.report_version,
        giza.operations.make.main,
        giza.operations.test.integration_main,
        giza.operations.changelog.main,
    ],
    'git': [
        giza.operations.git.apply_patch,
        giza.operations.git.pull_rebase,
        giza.operations.git.cherry_pick,
        giza.operations.git.merge,
        giza.operations.git.create_branch,
    ],
    'cr': [
        giza.operations.code_review.create_or_update,
        giza.operations.code_review.list_reviews,
        giza.operations.code_review.close,
        giza.operations.code_review.checkout,
    ],
    'generate': [
        giza.operations.generate.assets,
        giza.operations.generate.images,
        giza.operations.generate.api,
        giza.operations.generate.intersphinx,
        giza.operations.generate.options,
        giza.operations.generate.migration,
        giza.operations.generate.steps,
        giza.operations.generate.tables,
        giza.operations.generate.toc,
        giza.operations.generate.examples,
        giza.operations.generate.redirects,
        giza.operations.generate.robots,
        giza.operations.generate.source,
        giza.operations.generate.sphinx,
        giza.operations.generate.release,
        giza.operations.generate.glossary,
        giza.operations.generate.changelogs,
    ],
    'includes': [
        giza.operations.includes.recursive,
        giza.operations.includes.changed,
        giza.operations.includes.once,
        giza.operations.includes.unused,
        giza.operations.includes.list,
        giza.operations.includes.graph,
        giza.operations.includes.clean,
    ],
    'packaging': [
        giza.operations.packaging.fetch,
        giza.operations.packaging.unwind,
        giza.operations.packaging.create,
        giza.operations.packaging.deploy,
    ],
    'env': [
        giza.operations.build_env.package,
        giza.operations.build_env.extract,
    ],
    'tx': [
        giza.operations.tx.check_orphaned,
        giza.operations.tx.update_translations,
        giza.operations.tx.update_translations_transifex,
        giza.operations.tx.pull_translations,
        giza.operations.tx.push_translations,
    ],
}


def get_base_parser():
    """
    Adds global arguments/settings giza build process, and creates the top-level
    argument parser object.
    """

    parser = argh.ArghParser()
    parser.add_argument('--level', '-l',
                        choices=['debug', 'warning', 'info', 'critical', 'error'],
                        default='info')
    parser.add_argument('--serial', '-s', default=None, dest='runner',
                        const='serial', action='store_const')
    parser.add_argument('--thread', default=None, dest='runner', const='thread',
                        action='store_const')
    parser.add_argument('--event', default=None, dest='runner', const='event', action='store_const')
    parser.add_argument('--process', default=None, dest='runner',
                        const='process', action='store_const')
    parser.add_argument('--force', '-f', default=False, action='store_true')
    parser.add_argument('--fast', action='store_true')

    return parser


def main():
    """
    The main entry point, as specified in the ``setup.py`` file. Adds commands
    from other subsidiary entry points (specified in the ``commands`` variable
    above,) and then uses ``arch.dispatch()`` to start the process.

    The ``RuntimeStateConfig()`` object is created here and handed to the parser
    as the object that will recive all command line data, rather than using a
    standard argparse namespace object. This allows all runtime argument parsing
    to happen inside of these config objects rather than spread among all of the
    entry points.

    This function catches and recovers from :exc:`KeyboardInterupt` which means
    that doesn't dump a stack trace following a Control-C.
    """

    parser = get_base_parser()

    for namespace, entry_points in commands.items():
        if namespace == 'main':
            argh.add_commands(parser, entry_points)
        else:
            argh.add_commands(parser, entry_points, namespace=namespace)

    args = RuntimeStateConfig()
    try:
        argh.dispatch(parser, namespace=args)
    except KeyboardInterrupt:
        logger.error('operation interrupted by user.')

if __name__ == '__main__':
    main()
