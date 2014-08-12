import logging

import argh

from giza.git import GitRepo
from giza.config.helper import fetch_config

logger = logging.getLogger('giza.operations.git')

@argh.arg('--branch', '-b', default=None, dest='git_branch')
@argh.arg('--patch', '-p', nargs='*', dest='git_objects')
@argh.arg('--signoff', '-s', default=False, action='store_true', dest='git_sign_patch')
@argh.named('am')
def apply_patch(args):
    c = fetch_config(args)

    g = GitRepo(c.paths.projectroot)

    if c.runstate.git_branch is None:
        c.runstate.git_branch = g.current_branch()

    with g.branch(c.runstate.git_branch):
        g.am(patches=c.runstate.git_objects,
             repo='/'.join(['http://github.com', c.git.remote.upstream]),
             sign=c.runstate.git_sign_patch)

@argh.arg('--branch', '-b', default=None, dest='git_branch')
@argh.named('update')
def pull_rebase(args):
    c = fetch_config(args)

    g = GitRepo(c.paths.projectroot)

    if c.runstate.git_branch is None:
        c.runstate.git_branch = g.current_branch

    with g.branch(c.runstate.git_branch):
        g.update()

@argh.arg('--branch', '-b', default=None, dest='git_branch')
@argh.arg('--commits', '-c', nargs='*', dest='git_objects')
@argh.named('cp')
def cherry_pick(args):
    c = fetch_config(args)

    g = GitRepo(c.paths.projectroot)

    if c.runstate.git_branch is None:
        c.runstate.git_branch = g.current_branch()

    with g.branch(c.runstate.git_branch):
        g.cherry_pick(c.runstate.git_objects)
