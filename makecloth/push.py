#!/usr/bin/python

import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))

from docs_meta import conf
from utils import get_conf_file, ingest_yaml, get_branch
from makecloth import MakefileCloth

m = MakefileCloth()

_check_dependency = set()

def add_dependency(data):
    if not isinstance(data['dependency'], list):
        data['dependency'] = [data['dependency']]

    phony = []
    dependency = []
    for dep in data['dependency']:
        if dep.endswith('if-up-to-date') and dep not in _check_dependency:
            env = data['env']
            m.target('_build-check-' + env)
            m.job('fab deploy.{0}:{1} deploy.check'.format(env, conf.git.branches.current))
            m.target(data['target'] + '-if-up-to-date', ['_build-check-' + env, 'publish'])
            _check_dependency.add(dep)

        dependency.append(dep)
        phony.append(dep)

    return { 'phony': phony, 'dep': dependency }

def is_recursive(options):
    if 'recursive' in options:
        return True
    else:
        return True

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


def get_local_path(options, *args):
    if 'branched' in options:
        return os.path.join(os.path.sep.join(args),
                            conf.git.branches.current)
    else:
        return os.path.sep.join(args)

def add_static_commands(paths):
    rstr = 'deploy.static:local="{1}",remote="{0}"'

    if isinstance(paths['static'], list):
        r = []
        for static_path in paths['static']:
            r.append(rstr.format(os.path.join(conf.build.paths.output, paths['local'], static_path),
                                 os.path.join(paths['remote'], static_path)))
        return ' '.join(r)
    else:
        return rstr.format(os.path.join(conf.build.paths.output, paths['local'], paths['static']),
                           os.path.join(paths['remote'], paths['static']))

###### primary builder generators ######

def generate_build_system(data):
    phony = []
    for builder in data:
        dep = add_dependency(builder)
        phony.extend(dep['phony'])
        dep = dep['dep']
        target = builder['target']

        push_cmd = ['fab']

        if is_recursive(builder['options']):
            push_cmd.append('deploy.recursive')
        if is_delete(builder['options']):
            push_cmd.append('deploy.delete')

        push_cmd.append( 'deploy.remote:"{0}"'.format(builder['env']))

        push_cmd.append('deploy.{0}:local="{1}",remote="{2}"'.format(build_type(builder['options']),
                                                                     get_local_path(builder['options'],
                                                                                    conf.build.paths.output,
                                                                                    builder['paths']['local']),
                                                                     builder['paths']['remote']))

        if 'static' in builder['paths']:
            push_cmd.append(add_static_commands(builder['paths']))

        phony.append(target)
        m.target(target, dep)
        m.msg('[{0}]: deploying "{1}" to the "{2}" environment'.format(target, conf.git.branches.current, builder['env']))
        m.job(' '.join(push_cmd))
        m.msg('[{0}]: deployed "{1}" to the "{2}" environment'.format(target, conf.git.branches.current, builder['env']))
        m.newline()

    m.target('.PHONY', phony)

def main():
    push_conf = ingest_yaml(get_conf_file(__file__))

    generate_build_system(push_conf)

    m.write(sys.argv[1])

    print('[meta-build]: built "' + sys.argv[1] + '" to specify dependencies  files.')

if __name__ == '__main__':
    main()
