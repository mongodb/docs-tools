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

from giza.libgiza.app import BuildApp
from giza.libgiza.git import GitRepo, GitError

from giza.config.helper import fetch_config
from giza.operations.sphinx_cmds import sphinx_publication
from giza.tools.files import safe_create_directory

logger = logging.getLogger('giza.operations.quickstart')


@argh.arg('--with-git', action='store_true', dest='quickstart_git')
@argh.named('quickstart')
@argh.expects_obj
def make_project(args):
    """
    Generate a project skeleton. Prefer this operation over
    ``sphinx-quickstart``. Also builds skeleton HTML artifacts.
    """
    if args.quickstart_git is True:
        logger.info('creating a new git repository')
        g = GitRepo(os.getcwd())
        g.create_repo()
        build_sphinx = True
    else:
        try:
            GitRepo().sha()
            build_sphinx = True
        except GitError:
            build_sphinx = False

    mod_path = os.path.dirname(inspect.getfile(giza))
    qstart_path = os.path.join(mod_path, 'quickstart')

    cmd = 'rsync --ignore-existing --recursive {0}/. {1}'.format(qstart_path, os.getcwd())
    r = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
    logger.info('migrated new site files')

    if args.quickstart_git is True:
        if not r.startswith('Reinitialized'):
            g.cmd('add', '-A')

            try:
                g.cmd('commit', '-m', '"initial commit"')
            except GitError:
                build_sphinx = False
                pass

    if build_sphinx is True:
        test_build_site(args)


def test_build_site(args):
    args.languages_to_build = args.editions_to_build = []
    args.builder = 'html'

    conf = fetch_config(args)

    safe_create_directory('build')
    with BuildApp.new(pool_type=conf.runstate.runner,
                      pool_size=conf.runstate.pool_size,
                      force=conf.runstate.force).context() as app:
        try:
            sphinx_publication(conf, args, app)
        except:
            sphinx_publication(conf, args, app)
            if os.path.exists('doc-tools'):
                shutil.rmtree('docs-tools')

    logger.info('bootstrapped makefile system')

    logger.info('updated project skeleton in current directory.')
