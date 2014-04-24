import os
import logging

logger = logging.getLogger(os.path.basename(__file__))


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

class GitRepo(object):
    def __init__(self, path=None):
        if path is None:
            self.path = os.getcwd()
        else:
            self.path = path

        logger.debug("created git repository management object for {0}".format(self.path))

    def cmd(self, *args):
        args = ' '.join(args)

        return command(command='cd {0} ; git {1}'.format(self.path, args), capture=True)

    def remotes(self):
        return self.cmd('remote').out.split('\n')

    def branch_file(self, path, branch='master'):
        return self.cmd('show {branch}:{path}'.format(branch=branch, path=path)).out

    def checkout(self, ref):
        return self.cmd('checkout', ref)

    def hard_reset(self, ref='HEAD'):
        return self.cmd('reset', '--hard', ref)

    def reset(self, ref='HEAD'):
        return self.cmd('reset', ref)

    def fetch(self, remote='origin'):
        return self.cmd('fetch', remote)

    def pull(self, remote='origin', branch='master'):
        return self.cmd('pull', remote, branch)

    def sha(self, ref='HEAD'):
        return self.cmd('rev-parse', '--verify', ref).out

    def clone(self, remote, repo_path=None, branch=None):
        args = ['clone', remote]

        if branch is not None:
            args.extend(['--branch', branch])

        if repo_path is not None:
            args.append(repo_path)

        return self.cmd(*args)
