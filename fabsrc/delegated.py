import os.path

from fabric.api import task, abort, env, hide

from utils.serialization import ingest_yaml
from utils.config import get_conf
from utils.sphinx import get_sphinx_builders
from utils.git import get_branch

from git import GitRepoManager

b = 'delegated-builder'

def build_branch(logfile, branch='master', target='publish', wait=False):
    print('[{0}]: building {1} check {2} for build log.'.format(b, branch, logfile))

    if wait is True:
        print('[{0}]: building now, waiting for the build to finish.'.format(b))

    cmd = ['make', target]
    with open(logfile, 'a') as f:
        f.write('[{0}]: --- logging {1} -- {1} ---\n'.format(b, branch, ' '.join(cmd)))

    log_command_output(cmd, env.repo.path, logfile, wait)

    if wait is False:
        print('[{0}]: build in progress.'.format(b))

env.logfile = None
env.builders = ['publish', 'push', 'stage', 'json-output']

try:
    env.builders.extend(get_sphinx_builders())
except IOError:
    env.builders.extend(['html', 'json', 'dirhtml', 'epub'])

env.branch = get_branch()
env.wait = False
env.repo = GitRepoManager()
env.repo.b = b

@task
def wait():
    "Optional. If specified, the delegated.build() operation will block until the build completes."
    env.wait = True

@task
def log(logfile):
    "Required. Specifies the path of the build log file."

    env.logfile = logfile

@task
def branch(branch):
    "Optional. Specify the name of the (publishable) branch to build."

    if branch in env.repo.branches:
        env.branch = branch
    else:
        abort(branch + ' is not in list of buildable branches.')

@task
def build(builder='publish'):
    "Required. Starts a build. Specify the builder to use as an argument."

    if env.logfile is None:
        env.logfile = os.path.join(get_conf().build.paths.output, 'docs-staging-delegated.log')

    if builder not in env.builders:
        pass
    else:
        with hide('running'):
            env.repo.set_branch(env.branch)
            env.repo.set_path(env.repo.delegated_path)
            env.repo.update_repo(logfile=env.logfile, branch=env.branch)

        build_branch(logfile=env.logfile, branch=env.branch, target=builder, wait=env.wait)
