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
Helpers and wrappers for performing common maintenance operations on a
repository with git.
"""

import logging
import os
import subprocess

import argh

from giza.libgiza.app import BuildApp
from giza.libgiza.git import GitRepo
from giza.config.helper import fetch_config
from giza.operations.build_env import fix_build_env_tasks, get_existing_builders

logger = logging.getLogger('giza.operations.git')


@argh.arg('--patch', '-p', nargs='*', dest='git_objects')
@argh.arg('--branch', '-b', nargs='*', dest='git_branch')
@argh.arg('--signoff', '-s', default=False, action='store_true', dest='git_sign_patch')
@argh.named('am')
@argh.expects_obj
def apply_patch(args):
    c = fetch_config(args)

    g = GitRepo(c.paths.projectroot)

    if c.runstate.git_branch is None:
        c.runstate.git_branch = [g.current_branch()]

    for branch in c.runstate.git_branch:
        with g.branch(branch):
            g.am(patches=c.runstate.git_objects,
                 repo='/'.join(['https://github.com', c.git.remote.upstream]),
                 sign=c.runstate.git_sign_patch)


@argh.arg('--branch', '-b', nargs="*", dest='git_branch')
@argh.named('update')
@argh.expects_obj
def pull_rebase(args):
    c = fetch_config(args)

    g = GitRepo(c.paths.projectroot)

    if c.runstate.git_branch is None:
        c.runstate.git_branch = [g.current_branch()]

    for branch in c.runstate.git_branch:
        with g.branch(branch):
            g.update()
            logger.info('updated: ' + branch)


@argh.arg('--branch', '-b', nargs="*", dest='git_branch')
@argh.arg('--commits', '-c', nargs='*', dest='git_objects')
@argh.named('cp')
@argh.expects_obj
def cherry_pick(args):
    c = fetch_config(args)

    g = GitRepo(c.paths.projectroot)

    if c.runstate.git_branch is None:
        c.runstate.git_branch = [g.current_branch()]

    for branch in c.runstate.git_branch:
        with g.branch(branch):
            g.cherry_pick(c.runstate.git_objects)


@argh.arg('--branch', '-b', default=None, dest='git_branch')
@argh.expects_obj
def merge(args):
    c = fetch_config(args)

    g = GitRepo(c.paths.projectroot)

    from_branch = g.current_branch()
    branch_name = str(id(c.runstate.git_branch))

    g.checkout_branch(branch_name, c.runstate.git_branch)

    try:
        g.checkout(branch_name)
        g.rebase(from_branch)
        g.checkout(from_branch)
        g.merge(c.runstate.git_branch)
        logger.info('rebased and merged {0} into {1}'.format(c.runstate.git_branch, from_branch))
    except Exception as e:
        logger.warning('error attempting to merge branch: ' + c.runstate.git_branch)
        logger.error(e)
    finally:
        if g.current_branch != from_branch:
            g.checkout(from_branch)

        g.remove_branch(branch_name, force=False)


@argh.expects_obj
@argh.named("setup-branches")
def setup_branches(args):
    conf = fetch_config(args)

    g = GitRepo(conf.paths.projectroot)

    if 'upstream' in g.remotes():
        remote = 'upstream'
    else:
        remote = 'origin'

    for pbranch in conf.git.branches.published:
        if g.branch_exists(pbranch):
            continue
        else:
            tracking_branch = '/'.join([remote, pbranch])
            g.create_branch(pbranch, tracking=tracking_branch)
            logger.info('created branch "{0}" tracking "{1}"'.format(pbranch, tracking_branch))


@argh.expects_obj
@argh.named("create-branch")
@argh.arg('git_branch')
def create_branch(args):
    """
    Takes a single branch name and (if necessary) creates a new branch. Then,
    populates the ``build/<branch>`` directory for the new branch using either
    the parent branch or ``master``. Safe to run multiple times (after a rebase)
    to update the build cache from master.

    Also calls :method:`~giza.operations.build_env.fix_build_environment()` to
    tweak the new build output to update hashes and on-disk copies of the
    environment to prevent unnecessary full-rebuilds from sphinx.
    """

    conf = fetch_config(args)

    g = GitRepo(conf.paths.projectroot)

    branch = conf.runstate.git_branch
    base_branch = g.current_branch()

    if base_branch == branch:
        base_branch = 'master'
        logger.warning('seeding build data for branch "{0}" from "master"'.format(branch))

    branch_builddir = os.path.join(conf.paths.projectroot,
                                   conf.paths.output, branch)

    base_builddir = os.path.join(conf.paths.projectroot,
                                 conf.paths.output, base_branch)

    if g.branch_exists(branch):
        logger.info('checking out branch "{0}"'.format(branch))
    else:
        logger.info('creating and checking out a branch named "{0}"'.format(branch))

    g.checkout_branch(branch)

    cmd = "rsync -r --times --checksum {0}/ {1}".format(base_builddir, branch_builddir)
    logger.info('seeding build directory for "{0}" from "{1}"'.format(branch, base_branch))

    try:
        subprocess.check_call(args=cmd.split())
        logger.info('branch creation complete.')
    except subprocess.CalledProcessError:
        logger.error(cmd)

    # get a new config here for the new branch
    conf = fetch_config(args)
    builders = get_existing_builders(conf)

    with BuildApp.new(pool_type='process',
                      pool_size=conf.runstate.pool_size,
                      force=conf.runstate.force).context() as app:
        app.exted_queue(fix_build_env_tasks(builders, conf))
