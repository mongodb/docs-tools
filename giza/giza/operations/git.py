import os.path
import logging

import argh

from giza.git import GitRepo
from giza.config.main import Configuration

logger = logging.getLogger('git-operations')

@argh.arg('--branch', '-b', default=None, dest='git_branch')
@argh.arg('--patch', '-p', nargs='*', dest='git_objects')
@argh.arg('--signoff', '-s', default=False, action='store_true', dest='git_sign_patch')
@argh.named('am')
def apply_patch(arg):
    c = Configuration()
    c.ingest(args.conf_path)
    c.runstate = args

    g = GitRepo(conf.paths.projectroot)

    if c.runstate.git_branch is None:
        c.runstate.git_branch = g.current_branch

    with g.branch(c.runstate.git_branch):
        g.am(patches=c.runstate.git_objects,
             repo='/'.join(['http://github.com', c.git.remote.upstream]),
             sign=c.runstate.git_sign_patch)

@argh.arg('--branch', '-b', default=None, dest='git_branch')
@argh.named('update')
def pull_rebase(arg):
    c = Configuration()
    c.ingest(args.conf_path)
    c.runstate = args

    g = GitRepo(conf.paths.projectroot)

    if c.runstate.git_branch is None:
        c.runstate.git_branch = g.current_branch

    with g.branch(c.runstate.git_branch):
        g.update()

@argh.arg('--branch', '-b', default=None, dest='git_branch')
@argh.arg('--commits', '-c', nargs='*', dest='git_objects')
@argh.named('cp')
def cherry_pick(arg):
    c = Configuration()
    c.ingest(args.conf_path)
    c.runstate = args

    g = GitRepo(conf.paths.projectroot)

    if c.runstate.git_branch is None:
        c.runstate.git_branch = g.current_branch

    with g.branch(c.runstate.git_branch):
        g.cherry_pick(c.runstate.git_objects)
