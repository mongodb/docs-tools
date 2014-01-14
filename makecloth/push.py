#!/usr/bin/python

import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin')))

from utils.config import get_conf
from utils.git import get_branch
from utils.serialization import ingest_yaml
from utils.structures import get_conf_file

from makecloth import MakefileCloth

m = MakefileCloth()
conf = get_conf()

##############################  Legacy Push Makefile Builder ##############################

## Leaving existing code in place for a while, but the following code now lives
## (in updated form) in the fabfile/deploy.program

_check_dependency = set()

def add_dependency(data):
    if not isinstance(data['dependency'], list):
        data['dependency'] = [data['dependency']]

    phony = []
    dependency = []
    for dep in data['dependency']:
        if dep.endswith('if-up-to-date') and dep not in _check_dependency:
            env = data['env']
            m.target(data['target'] + '-if-up-to-date', ['publish'])
            _check_dependency.add(dep)

        dependency.append(dep)
        phony.append(dep)

    return { 'phony': phony, 'dep': dependency }

##############################  New Style Push Commands ##############################

def generate_new_deploy_system(push_conf):
    phony = []
    for job in push_conf:
        dep = add_dependency(job)
        phony.extend(dep['phony'])
        dep = dep['dep']
        t = job['target']

        m.target(t, dep)
        m.job('fab deploy:{0}'.format(t))
        m.newline()

    m.target('.PHONY', phony)

def main():
    push_conf = ingest_yaml(get_conf_file(file=__file__, directory=conf.paths.builddata))

    generate_new_deploy_system(push_conf)

    m.write(sys.argv[1])

    print('[meta-build]: built "' + sys.argv[1] + '" to specify dependencies  files.')

if __name__ == '__main__':
    main()
