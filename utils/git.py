import os

try:
    from utils.shell import command
except ImportError:
    from shell import command

def get_commit(path=None):
    return command('git rev-parse --verify HEAD', capture=True).out

def get_branch(path=None):
    return command('git symbolic-ref HEAD', capture=True).out.split('/')[2]

def checkout_file(path, branch='master'):
    return command(command='git checkout {0} -- {1}'.format(branch, path),
                   capture=False, ignore=False)

def get_file_from_branch(path, branch='master'):
    cmd = 'git show {branch}:{path}'.format(branch=branch, path=path)

    return command(command=cmd, capture=True, ignore=False).out
