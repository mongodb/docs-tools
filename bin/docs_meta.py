#!/usr/bin/python

import datetime
import argparse
import yaml
import os.path
import sys
from utils import write_yaml, shell_value, get_commit, get_branch, get_conf_file, ingest_yaml, BuildConfiguration

### Configuration and Settings

# For backwards compatibility, populating global variables from yaml file. See
# the docs_meta.yaml file for documentation of these values.

### Functions

def get_sphinx_builders(conf=None):
    if conf is None:
        conf = get_conf()

    path = os.path.join(conf.build.paths.projectroot, conf.build.paths.builddata, 'sphinx.yaml')
    return ingest_yaml(path)['builders']

def get_manual_path(conf=None):
    if conf is None:
        conf = load_conf()

    if conf.project.name in ['about', 'ecosystem']:
        return conf.project.name

    branch = get_branch()

    if branch == conf.git.branches.manual:
        if conf.project.name == 'mms' or conf.project.name == 'meta-driver':
            return 'current'
        else:
            return 'manual'
    else:
        return branch

def load_conf():
    try:
        project_root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
        conf = BuildConfiguration(filename='docs_meta.yaml',
                                  directory=os.path.join(project_root_dir, 'bin'))
    except IOError:
        project_root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
        conf = BuildConfiguration(filename='docs_meta.yaml',
                                  directory=os.path.join(project_root_dir, 'bin'))

    conf.build.paths.projectroot = project_root_dir

    return conf

def get_conf():
    conf = load_conf()

    if os.path.exists('/etc/arch-release'):
        conf.build.system.python = 'python2'
    else:
        conf.build.system.python = 'python'

    conf.git.branches.current = get_branch()
    conf.git.commit = get_commit()

    conf.build.paths.update(render_paths('dict'))

    return conf

def get_versions(conf=None):
    if conf is None:
        conf = load_conf()

    o = []

    for version in conf.version.published:
        version_string = str(version)

        if version_string in ['current', 'master', 'upcoming']:
            path_name = version_string
        else:
            path_name = 'v' + version_string

        if conf.git.remote.upstream.endswith('mms-docs'):
            pass
        else:
            if version == conf.version.stable:
                version_string += ' (current)'
            if version == conf.version.upcoming:
                version_string += ' (upcoming)'

        o.append( { 'v': path_name, 't': version_string } )

    return o

def output_yaml(fn, conf=None):
    if conf is None:
        conf = load_conf()

    o = {
            'branch': get_branch(),
            'commit': get_commit(),
            'manual_path': get_manual_path(),
            'date': str(datetime.date.today().year),
            'version_selector': get_versions(),
            'stable': conf.version.stable,
            'upcoming': conf.version.upcoming,
            'published_branches': conf.git.branches.published,
            'pdfs': []
    }

    write_yaml(o, fn)

def render_paths(fn, conf=None):
    if conf is None:
        conf = load_conf()

    paths = conf.build.paths

    paths.public = os.path.join(paths.output, 'public')
    paths.branch_output = os.path.join(paths.output, get_branch())
    paths.branch_source = os.path.join(paths.branch_output, 'source')
    paths.branch_staging = os.path.join(paths.public, get_branch())

    public_site_output = {
        'manual': os.path.join(paths.output, 'public', get_branch()),
        'ecosystem': os.path.join(paths.output, 'public'),
        'about': os.path.join(paths.output, 'public'),
        'meta-driver': os.path.join(paths.output, 'public', get_branch()),
        'mms': paths.public,
    }

    try:
        paths.public_site_output = public_site_output[conf.project.name]
    except KeyError:
        paths.public_site_output = paths.public

    if conf.project.name == 'mms':
        conf.build.paths.mms = {
            'hosted': os.path.join(paths.output, 'public', 'hosted', get_branch()),
            'saas': os.path.join(paths.output, 'public', 'saas')
        }

    # for backwards compatibility
    paths['branch-staging'] = paths.branch_staging
    paths['branch-output'] = paths.branch_output
    paths['branch-source'] = paths.branch_source

    if str(fn).endswith('yaml'):
        utils.write_yaml(dict(paths), fn)
    elif fn == 'print':
        print(yaml.safe_dump(dict(paths), default_flow_style=False) + '...')
    else:
        return paths

def main():
    action_list = [ 'branch', 'commit', 'versions', 'stable', 'all', 'manual',
                    'yaml', 'current-or-manual', 'output', 'paths']

    parser = argparse.ArgumentParser('MongoDB Documentation Meta Data Provider')
    parser.add_argument('action', choices=action_list, nargs='?', default='all')
    parser.add_argument('filename', nargs='?', default='meta.yaml')

    ui = parser.parse_args()

    if ui.action == 'all':
        BREAK = "\n"
        print("MongoDB Manual:" + BREAK +
              "     Commit: " + get_commit() + BREAK +
              "     Branch: " + get_branch() + BREAK +
              "     Manual: " + conf.git.branches.manual + BREAK +
              "     Versions: " + str(conf.version.published) + BREAK +
              "     Stable: " + str(conf.version.stable) + BREAK +
              "     Year: " + str(datetime.date.today().year) + BREAK +
              "     Path: " + get_manual_path() + BREAK +
              "     Version UI: " + str(get_versions()))
    elif ui.action == 'branch':
        print(get_branch())
    elif ui.action == 'commit':
        print(get_commit())
    elif ui.action == 'stable':
        print(conf.version.stable)
    elif ui.action == 'versions':
        print(conf.version.published)
    elif ui.action == 'manual':
        print(conf.git.branches.manual)
    elif ui.action == 'current-or-manual':
        print(get_manual_path())
    elif ui.action == 'yaml':
        output_yaml(ui.filename)
    elif ui.action == 'paths':
        render_paths('print')

if __name__ == '__main__':
    main()
