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
Provides a multipurpose build-directory cleanup operation that removes build
directories on a per-builder or per-branch basis, and is also capable of
removing branches that haven't been used in a certain number of days.
"""

import os
import logging
import shutil

import argh

from libgiza.app import BuildApp
from giza.config.helper import fetch_config, get_builder_jobs
from giza.config.sphinx_config import resolve_builder_path

logger = logging.getLogger('giza.operations.clean')


@argh.arg('--builder', '-b')
@argh.arg('--git_branch', default=None)
@argh.arg('--edition', '-e', nargs='*', dest='editions_to_build')
@argh.arg('--language', '-l', nargs='*', dest='languages_to_build')
@argh.arg('--length', default=None, type=int, dest='days_to_save')
@argh.named('clean')
@argh.expects_obj
def main(args):
    """
    Removes build artifacts from ``build/`` directory.
    """

    c = fetch_config(args)
    app = BuildApp.new(pool_type=c.runstate.runner,
                       pool_size=c.runstate.pool_size,
                       force=c.runstate.force)

    to_remove = set()

    if c.runstate.git_branch is not None:
        to_remove.add(os.path.join(c.paths.projectroot, c.paths.branch_output))

    if c.runstate.builder != []:
        for edition, language, builder in get_builder_jobs(c):
            builder_path = resolve_builder_path(builder, edition, language, c)
            builder_path = os.path.join(c.paths.projectroot, c.paths.branch_output, builder_path)

            to_remove.add(builder_path)
            dirpath, base = os.path.split(builder_path)
            to_remove.add(os.path.join(dirpath, 'doctrees-' + base))

            m = 'remove artifacts associated with the {0} builder in {1} ({2}, {3})'
            logger.debug(m.format(builder, c.git.branches.current, edition, language))

    if c.runstate.days_to_save is not None:
        published_branches = ['docs-tools', 'archive', 'public', 'primer', c.git.branches.current]
        published_branches.extend(c.git.branches.published)

        for build in os.listdir(os.path.join(c.paths.projectroot, c.paths.output)):
            build = os.path.join(c.paths.projectroot, c.paths.output, build)
            branch = os.path.split(build)[1]

            if branch in published_branches:
                continue
            elif not os.path.isdir(build):
                continue
            elif os.stat(build).st_mtime > c.runstate.days_to_save:
                to_remove.add(build)
                to_remove.add(os.path.join(c.paths.projectroot, c.paths.output, 'public', branch))
                logger.debug('removed stale artifacts: "{0}" and "build/public/{0}"'.format(branch))

    for fn in to_remove:
        if os.path.isdir(fn):
            job = shutil.rmtree
        else:
            job = os.remove

        t = app.add('task')
        t.job = job
        t.args = fn
        m = 'removing artifact: {0}'.format(fn)
        t.description = m
        logger.critical(m)

    app.run()
