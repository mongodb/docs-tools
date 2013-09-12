import os.path
import re
import json
from fabric.api import task, local, puts, lcd, env, abort
from docs_meta import get_conf
from utils import expand_tree
from process import munge_page

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

@task
def tags():
    conf = get_conf()

    regexp_fn = os.path.join(os.path.join(conf.build.paths.projectroot, 
                                        conf.build.paths.tools, 'etags.regexp'))

    if not os.path.exists(regexp_fn):
        abort('[dev]: cannot regenerate TAGS: no {0} file'.format(regexp_fn))

    source = expand_tree(os.path.join(conf.build.paths.projectroot,
                                      conf.build.paths.source), 'txt')

    if len(source) == 0:
        abort('[dev]: no source files in {0}'.format(source))

    source = ' '.join(source)

    local('etags -I --language=none --regex=@{0} {1}'.format(regexp_fn, source))
    
    regexps = [
        (re.compile(r'\.\. (.*):: \$*(.*)'), r'\1.\2'),
        (re.compile(r'\.\. _(.*)'), r'ref.\1')
    ]

    munge_page(fn=os.path.join(conf.build.paths.projectroot, 'TAGS'), 
               regex=regexps,
               tag='dev')
