import os.path
import re
import json
import time
import logging

logger = logging.getLogger(os.path.basename(__file__))

from fabric.api import task, local, puts, lcd, env, abort

from fabfile.utils.transformations import munge_page

from fabfile.utils.files import expand_tree
from fabfile.utils.config import get_conf
from fabfile.utils.project import edition_setup

env.dev_repo = os.path.abspath(os.path.join(os.path.split(os.path.abspath(__file__))[0], '..', '..', 'docs-tools'))

@task
def bootstrap(action='setup'):
    "Wrapper around the 'bootstrap.py' operation."

    cmd = ['python bootstrap.py']

    if action in ['setup', 'clean', 'safe']:
        cmd.append(action)


    else:
        abort('[docs-tools]: invalid bootstrap action')

    with lcd(get_conf().build.paths.projectroot):
        local(' '.join(cmd))






@task
def conf(edition=None, conf=None):
    "Returns the build configuration object for visual introspection. Optionally specify 'edition' argument."

    if conf is None:
        conf = get_conf()
    if edition is not None:
        conf = edition_setup(edition, conf)

    puts(json.dumps(conf, indent=3))

@task
def tags():
    "Uses 'etags' to generate a TAG index to aid navigation."

    conf = get_conf()

    regexp_fn = os.path.join(os.path.join(conf.paths.projectroot,
                                          conf.paths.tools, 'etags.regexp'))

    if not os.path.exists(regexp_fn):
        abort('[dev]: cannot regenerate TAGS: no {0} file'.format(regexp_fn))

    source = expand_tree(os.path.join(conf.paths.projectroot,
                                      conf.paths.source), 'txt')

    if len(source) == 0:
        abort('[dev]: no source files in {0}'.format(source))

    source = ' '.join(source)

    local('etags -I --language=none --regex=@{0} {1}'.format(regexp_fn, source))

    regexps = [
        (re.compile(r'\.\. (.*):: \$*(.*)'), r'\1.\2'),
        (re.compile(r'\.\. _(.*)'), r'ref.\1')
    ]

    munge_page(fn=os.path.join(conf.paths.projectroot, 'TAGS'),
               regex=regexps,
               tag='dev')

class Timer():
    def __init__(self, name=None, report=True):
        self.report = report
        if name is None:
            self.name = 'task'
        else:
            self.name = name
    def __enter__(self):
        self.start = time.time()
    def __exit__(self, *args):
        message = '[build] [timer]: time elapsed for {0} was: {1}'
        message = message.format(self.name, str(time.time() - self.start))

        logger.debug(message)
        if self.report is True:
            print(message)
