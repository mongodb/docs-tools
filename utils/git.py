import os

from utils.shell import shell_value

def get_commit(path=None):
    if path is None:
        path = os.getcwd()

    return shell_value('git rev-parse --verify HEAD', path)

def get_branch(path=None):
    if path is None:
        path = os.getcwd()

    return shell_value('git symbolic-ref HEAD', path).split('/')[2]

