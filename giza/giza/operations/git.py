import logging

import argh

from giza.core.git import GitRepo
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

@argh.arg('--branch', '-b', default=None, dest='git_branch')
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

        g.remove_branch(branch_name, force=True)
