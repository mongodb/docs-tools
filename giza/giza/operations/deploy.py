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

"""
Entry points that send locally built content to web servers.
"""

import logging

import argh
import onetimepass as otp

from giza.config.helper import fetch_config, new_credentials_config
from libgiza.app import BuildApp
from giza.deploy import Deploy, deploy_target
from giza.operations.sphinx_cmds import sphinx_publication

logger = logging.getLogger('giza.operations.deploy')


@argh.arg('--target', '-t', nargs='*', dest='push_targets')
@argh.arg('--dry-run', '-d', action='store_true', dest='dry_run')
@argh.named('deploy')
@argh.expects_obj
def main(args):
    """
    Uploads all build artifacts to the production environment. Does not build or
    render artifacts.
    """

    c = fetch_config(args)
    app = BuildApp.new(pool_type=c.runstate.runner,
                       pool_size=c.runstate.pool_size,
                       force=c.runstate.force)

    deploy_tasks(c, app)

    if c.runstate.dry_run is False:
        app.run()


@argh.arg('--deploy', '-d', nargs='*', dest='push_targets')
@argh.arg('--edition', '-e', nargs='*', dest='editions_to_build')
@argh.arg('--language', '-l', nargs='*', dest='languages_to_build')
@argh.arg('--builder', '-b', nargs='*', default='html')
@argh.arg('--serial_sphinx', action='store_true')
@argh.named('push')
@argh.expects_obj
def publish_and_deploy(args):
    """
    Combines the work of ``giza sphinx`` and ``giza deploy``, to produce build
    artifacts and then upload those artifacts to the servers.
    """

    c = fetch_config(args)
    app = BuildApp.new(pool_type=c.runstate.runner,
                       pool_size=c.runstate.pool_size,
                       force=c.runstate.force)

    sphinx_ret = sphinx_publication(c, app)
    if sphinx_ret == 0 or c.runstate.force is True:
        deploy_tasks(c, app)

        if c.runstate.dry_run is False:
            app.run()
    else:
        logger.warning(sphinx_ret + ' sphinx build(s) failed, and build not forced. not deploying.')


def deploy_tasks(c, app):
    """
    Deploys the build. The logic for generating the rsync commands is
    in ``giza.deploy``, and the configuration data is typically in
    ``config/push``.

    This function glues the config with the rsync command creation and then
    runs the commands.
    """
    pconf = dict((item['target'], item) for item in c.system.files.data.push)

    for target in c.runstate.push_targets:
        d = Deploy(c)

        target_pconf = pconf[target]

        if target_pconf['env'] == 'publication':
            target_pconf['env'] = 'production'

        d.load(target_pconf)

        for cmd in d.deploy_commands():
            task = app.add('task')
            task.args = ' '.join(cmd)
            task.job = deploy_target

            if c.runstate.dry_run is True:
                logger.info('dry run: {0}'.format(' '.join(cmd)))

    logger.info('completed deploy for: {0}'.format(' '.join(c.runstate.push_targets)))


@argh.named('code')
@argh.expects_obj
def twofa_code(args):
    "Returns a 2 factor authentication code."

    creds = new_credentials_config()

    print(otp.get_totp(creds.corp.seed))
