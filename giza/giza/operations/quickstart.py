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
Simple operations to create and bootstrap the content for new projects.
"""

import inspect
import logging
import os
import shutil
import subprocess

import argh
import giza

from libgiza.app import BuildApp
from libgiza.git import GitRepo, GitError

from giza.config.helper import fetch_config
from giza.operations.sphinx_cmds import sphinx_publication
from giza.tools.command import command, CommandError

logger = logging.getLogger('giza.operations.quickstart')


@argh.arg('--with-git', action='store_true', dest='quickstart_git')
@argh.named('quickstart')
@argh.expects_obj
def make_project(args):
    """
    Generate a project skeleton. Prefer this operation over
    ``sphinx-quickstart``. Also builds skeleton HTML artifacts.
    """
    _weak_bootstrapping(args)

    if args.quickstart_git is True:
        logger.info('creating a new git repository')
        g = GitRepo(os.getcwd())
        g.create_repo()

        if not r.out.startswith('Reinitialized'):
            g.cmd('add', '-A')

            try:
                g.cmd('commit', 'm', '"initial commit"')
            except GitError:
                pass


def _weak_bootstrapping(args):
    args.languages_to_build = args.editions_to_build = []
    args.builder = 'html'
    conf = fetch_config(args)

    app = BuildApp.new(pool_type=conf.runstate.runner,
                       pool_size=conf.runstate.pool_size,
                       force=conf.runstate.force)

    mod_path = os.path.dirname(inspect.getfile(giza))
    qstart_path = os.path.join(mod_path, 'quickstart')

    cmd = 'rsync --ignore-existing --recursive {0}/. {1}'.format(qstart_path, os.getcwd())
    subprocess.call(cmd.split())

    logger.info('migrated new site files')

    try:
        sphinx_publication(conf, args, app)
    except:
        sphinx_publication(conf, args, app)
        shutil.rmtree('docs-tools')

    command('python build/docs-tools/makecloth/meta.py build/makefile.meta')
    logger.info('bootstrapped makefile system')

    logger.info('updated project skeleton in current directory.')
