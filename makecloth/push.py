#!/usr/bin/python

import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))

from docs_meta import get_conf
from utils import get_conf_file, ingest_yaml, get_branch
from makecloth import MakefileCloth

m = MakefileCloth()
conf = get_conf()

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

def is_recursive(options):
    if 'recursive' in options:
        return True
    else:
        return False

def is_delete(options):
    if 'delete' in options:
        return True
    else:
        return False

def build_type(options):
    if 'static' in options:
        return 'static'
    else:
        return 'push'

def get_branched_path(options, *args):
    if 'branched' in options:
        return os.path.join(os.path.sep.join(args),
                            conf.git.branches.current)
    else:
        return os.path.sep.join(args)

def add_static_commands(paths):
    rstr = 'deploy.static:local_path="{0}",remote="{1}"'

    if isinstance(paths['static'], list):
        r = []
        for static_path in paths['static']:
            if static_path in ['manual', 'current']:
                remote_string = paths['remote']
            else:
                remote_string = os.path.join(paths['remote'], static_path)

            r.append(rstr.format(os.path.join(conf.build.paths.output, paths['local'], static_path),
                                 remote_string))
        return ' '.join(r)
    else:
        if paths['static'] in ['manual', 'current']:
            remote_string = paths['remote']
        else:
            remote_string = os.path.join(paths['remote'], paths['static'])

        return rstr.format(os.path.join(conf.build.paths.output, paths['local'], paths['static']),
                           remote_string)

###### primary builder generators ######

def generate_build_system(data):
    phony = []
    for builder in data:
        dep = add_dependency(builder)
        phony.extend(dep['phony'])
        dep = dep['dep']
        target = builder['target']

        push_cmd = ['fab']

        push_cmd.append('git.branch:' + get_branch())

        if 'edition' in builder:
            push_cmd.append('sphinx.edition:' + builder['edition'])

        if is_recursive(builder['options']):
            push_cmd.append('deploy.recursive')

        if is_delete(builder['options']):
            push_cmd.append('deploy.delete')

        push_cmd.append('deploy.remote:"{0}"'.format(builder['env']))
        push_cmd.append('deploy.{0}:local_path="{1}",remote="{2}"'.format(build_type(builder['options']),
                                                                          get_branched_path(builder['options'],
                                                                                            conf.build.paths.output,
                                                                                            builder['paths']['local']),
                                                                          get_branched_path(builder['options'],
                                                                                            builder['paths']['remote'])))

        if 'static' in builder['paths']:
            push_cmd.append(add_static_commands(builder['paths']))

        phony.append(target)
        m.target(target, dep)
        m.job(' '.join(push_cmd))
        m.newline()

    m.target('.PHONY', phony)

def main():
    push_conf = ingest_yaml(get_conf_file(__file__))

    generate_build_system(push_conf)

    m.write(sys.argv[1])

    print('[meta-build]: built "' + sys.argv[1] + '" to specify dependencies  files.')

if __name__ == '__main__':
    main()
