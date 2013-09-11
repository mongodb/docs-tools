import os.path
import json
from fabric.api import task, local, puts, lcd, env
from docs_meta import get_conf

env.dev_repo = os.path.abspath(os.path.join(os.path.split(os.path.abspath(__file__))[0], '..', '..', 'docs-tools'))

@task
def dev():
    if not os.path.exists(env.dev_repo):
        abort('[docs-tools]: a dev docs-tools branch does not exist.')
    with lcd(get_conf().build.paths.buildsystem):
        local('git remote set-url origin {0}/.git'.format(env.dev_repo))
        puts('[docs-tools]: set docs-tools repository to use a local remote.')

@task
def reset():
    with lcd(get_conf().build.paths.buildsystem):
        local('git remote set-url origin git@github.com:{0}.git'.format(conf.git.remote.tools))
        puts('[docs-tools]: set docs-tools to use the canonical remote.')

@task
def bootstrap(action='setup'):
    cmd = ['python bootstrap.py']

    if action in ['setup', 'clean']:
        cmd.append(action)
    else:
        abort('[docs-tools]: invalid bootstrap action')

    with lcd(get_conf().build.paths.projectroot):
        local(' '.join(cmd))

@task
def conf():
    conf = get_conf()
    puts(json.dumps(conf, indent=3))
