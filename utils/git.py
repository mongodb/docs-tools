import os

try:
    from utils.shell import shell_value, command
except ImportError:
    from shell import shell_value, command

def get_commit(path=None):
    if path is None:
        path = os.getcwd()

    return shell_value('git rev-parse --verify HEAD', path)

def get_branch(path=None):
    if path is None:
        path = os.getcwd()

    return shell_value('git symbolic-ref HEAD', path).split('/')[2]

def checkout_file(path, branch='master'):
    return command(command='git checkout {0} -- {1}'.format(branch, path),
                   capture=False, ignore=False)

def get_file_from_branch(path, branch='master'):
    cmd = 'git show {branch}:{path}'.format(branch=branch, path=path)
    out = command(command=cmd, capture=True, ignore=False)

    return out.out
