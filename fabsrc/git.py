import os.path
import re

from fabric.api import lcd, local, task, abort, env, hide
from fabric.utils import puts

from fabfile.utils.git import get_branch
from fabfile.utils.config import lazy_conf

env.sign = False
env.branch = None

@task
def sign():
    "For git.am(), sets the --signoff option."
    env.sign = True

@task
def am(obj,repo=None):
    "Runs 'git am' on a github object."

    if repo is None:
        repo = lazy_conf().git.remote.upstream

    cmd = ['curl',
           'https://github.com/{0}/'.format(repo),
           '|', 'git', 'am',
           '--signoff --3way' if env.sign else '--3way' ]

    if env.branch is not None:
        local('git checkout {0}'.format(env.branch))

    if obj.startswith('http'):
        cmd[1] = obj
        if not obj.endswith('.patch'):
            cmd[1] += '.patch'
        local(' '.join(cmd))
    elif re.search('[a-zA-Z]+', obj):
        cmd[1] = cmd[1] + 'commit/' + obj + '.patch'

        local(' '.join(cmd))
        puts('[git]: merged commit {0} for {1} into {2}'.format(obj, repo, get_branch()))
    else:
        cmd[1] = cmd[1] + 'pull/' + obj + '.patch'

        local(' '.join(cmd))
        puts('[git]: merged pull request #{0} for {1} into {2}'.format(obj, repo, get_branch()))

@task
def branch(branch):
    "Sets a branch to apply a git operation and is a no-op unless run with another operation."

    with hide('running'):
        branches = local("git for-each-ref  refs/heads/ --format='%(refname:short)'", capture=True).split()

        if branch not in branches:
            abort('{0} is not a local git branch'.format(branch))
        else:
            env.branch = branch

@task
def cp(*obj):
    "Runs git cherry-pick on a given commit."

    with hide('running'):
        if env.branch is not None:
            local('git checkout {0}'.format(env.branch))

        for commit in [ o for o in obj ]:
            local('git cherry-pick {0}'.format(commit))

        if env.branch is not None:
            local('git checkout -')
