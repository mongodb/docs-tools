import os

try:
    from shell import shell_value, command
except ImportError:
    # so bootstrapping works
    from utils.shell import shell_value, command

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


## The GitRepoManager class is used to interface with git repositories for the
## purpose of the delegated build system, that builds output from a checkout of
## the local repository with a different set of working files, so that
## multi-branch local builds need not overlap with the current work. See
## fabfile/delegated.py for the delegated builder.

class GitRepoManager(object):
    def __init__(self, path=None, branch='master'):
        self.delegated_path = os.path.join(os.getcwd(), 'build/.docs-staging')
        self.delegated_build_path = os.path.join(self.delegated_path, 'build')
        self.b = 'git'

        self.current_branch = get_branch(os.getcwd())
        self.branch = self.current_branch

        self.branches = set()
        self.branches.add(self.current_branch)
        for branch in lazy_conf().git.branches.published:
            if branch is not None:
                self.branches.add(branch)

        self.set_branch(branch)

        self.path = None
        self.set_path(path)

    def set_branch(self, branch='master'):
        if branch is None or branch == self.branch:
            pass
        elif branch != self.branch:
            self.branch = branch
        else:
            branch = os.getcwd()
            self.branch = branch

        if self.branch not in self.branches:
            if self.branch is not None:
                self.branches.add(self.branch)

    def set_path(self, path=None):
        if path is None or path == self.path:
            pass
        elif path != self.path:
            self.path = path
        else:
            path = os.getcwd()
            self.path = path

    def change_branch(self, branch=None):
        if branch == None:
            pass
        else:
            self.set_branch(branch)
            print('[{0}]: changing branch in {1} to "{2}"'.format(self.b, self.path, self.branch))

            with lcd(self.path):
                command('git checkout {0}'.format(str(self.branch)))

            print('[{0}]: checked out branch: {1} in staging.'.format(self.b, self.branch))

    @staticmethod
    def get_branches(path):
        with lcd(path):
            o = command('ls .git/refs/heads', capture=True)

        return o.stdout.split()

    def branch_cleanup(self, path=None):
        self.set_path(path)
        print('[{0}]: doing branch cleanup in {1}'.format(self.b, self.path))

        for branch in self.branches:
            if branch not in self.get_branches(self.path):
                self.create_branch(branch)

        for branch in self.get_branches(self.path):
            if branch != self.branch and branch not in self.branches:
                self.remove_branch(branch)

    def remove_branch(self, branch):
        with lcd(self.path):
            command('git branch -D {0}'.format(branch))

        print('[{0}]: cleaned up stale branch: {1}'.format(self.b, branch))

    def create_branch(self, branch):
        with lcd(self.path):
            command('git branch {0} origin/{0}'.format(branch))

        print('[{0}]: created {1} branch in repo {2}'.format(self.b, branch, self.path))

    def clone_repo(self, source, location):
        command('git clone {0} {1}'.format(source, location))
        print('[{0}]: created a clone of "{1}" repo in "{1}".'.format(self.b, source, location))
        self.set_path(location)

    def fetch(self, remote='origin'):
        with lcd(self.path):
            command('git fetch {0}'.format(remote))

    def reset(self, remote='origin'):
        with lcd(self.path):
            command('git reset --hard')
            command('git checkout {0}'.format(self.branch))
            command('git reset --hard {0}'.format('/'.join([remote, self.branch])))

    def reset_working_copy(self):
        self.fetch()
        self.reset()

    def create_staging_build_path(self):
        if os.path.exists(self.delegated_build_path):
            if os.path.islink(self.delegated_build_path):
                pass
            elif os.path.isdir(self.delegated_build_path):
                abort("[{0}]: ERROR: the path '{1}' is a directory, you probably want to remove it and try again.".format(self.b, self.delegated_build_path))
            else:
                abort("[{0}]: ERROR: check '{1}' and try again.".format(self.b, self.delegated_build_path))
        else:
            old_path = os.getcwd()
            os.chdir(os.path.join(old_path, self.delegated_path))
            os.symlink('../../build', 'build')
            os.chdir(old_path)
            print('[{0}] created "{1}" symlink.'.format(self.b, self.delegated_build_path))

    def update_repo(self, logfile=None, branch='master'):
        self.set_branch(branch)

        if self.path is None or not os.path.isdir(self.path):
            self.clone_repo('./', 'build/.docs-staging')
        else:
            with hide('running', 'stdout', 'stderr'):
                self.reset_working_copy()
            print('[{0}]: updated staging.'.format(self.b))

        self.create_staging_build_path()

        print('[{0}]: regenerated buildsystem'.format(self.b))

        with hide('running', 'stdout', 'stderr'):
            self.branch_cleanup(self.path)
            self.change_branch(branch)
