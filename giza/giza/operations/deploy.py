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
Entry points that

"""


import os.path
import logging
logger = logging.getLogger('giza.operations.deploy')

from giza.config.helper import fetch_config, new_credentials_config
from giza.core.app import BuildApp
from giza.deploy import Deploy, deploy_target
from giza.operations.sphinx_cmds import sphinx_publication
from giza.tools.command import command
from giza.tools.serialization import ingest_yaml_list, dict_from_list

import argh
import onetimepass as otp

@argh.arg('--target', '-t', nargs='*', dest='push_targets')
@argh.arg('--dry-run', '-d', action='store_true', dest='dry_run')
@argh.named('deploy')
@argh.expects_obj
def main(args):
    """
    Entry point for the deploy operation which just uploads the
    appropriate (defined in the projects ``config/push.yaml``) files
    from ``build/public/`` to the web servers.

    The work of the deploy operation itself is in ``deploy_worker()``
    """

    c = fetch_config(args)
    app = BuildApp(c)

    deploy_worker(c, app)

@argh.arg('--deploy', '-d', nargs='*', dest='push_targets')
@argh.arg('--edition', '-e', nargs='*', dest='editions_to_build')
@argh.arg('--language', '-l', nargs='*',dest='languages_to_build')
@argh.arg('--builder', '-b', nargs='*', default='html')
@argh.arg('--serial_sphinx', action='store_true')
@argh.named('push')
@argh.expects_obj
def publish_and_deploy(args):
    """
    Combines the work of the Sphinx builder (in
    ``giza.operations.sphinx_cmds.sphinx_publication``) with
    ``deploy_worker()``

    Essentially this is the same as calling: ::

       make publish
       make deploy

    Historically the build system has provided a ``push`` target for this functionality.
    """

    c = fetch_config(args)
    app = BuildApp(c)

    sphinx_ret = sphinx_publication(c, args, app)
    if sphinx_ret == 0 or c.runstate.force is True:
        deploy_worker(c, app)
    else:
        logger.warning(sphinx_ret + ' sphinx build(s) failed, and build not forced. not deploying.')

def deploy_worker(c, app):
    """
    Deploys the build. The logic for generating the rsync commands is
    in ``giza.deploy``, and the configuration data is typically in
    ``config/push``.

    This function glues the config with the rsync command creation and then
    runs the commands.
    """

    pconf = c.system.files.data.push
    pconf = dict_from_list('target', pconf)

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
            task.target = ""
            task.depends = os.path.join(c.paths.projectroot, c.paths.public_site_output)

            if c.runstate.dry_run is True:
                logger.info('dry run: {0}'.format(' '.join(cmd)))

    if c.runstate.dry_run is False:
        app.run()

    logger.info('completed deploy for: {0}'.format(' '.join(c.runstate.push_targets)))

@argh.named('code')
@argh.expects_obj
def twofa_code(args):
    """
    Returns a 2 factor authentication code using the ``otp`` package
    and access to credentials.
    """

    creds = new_credentials_config()

    print(otp.get_totp(creds.corp.seed))
