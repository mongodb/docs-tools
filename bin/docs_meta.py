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
        conf = get_conf()

    if conf.build.system.branched is False:
        return conf.project.tag
    else:
        branch = get_branch()

        o = []

        if conf.project.name in ['mms', 'meta-driver']:
            o.append(conf.project.tag)

        if branch == conf.git.branches.manual:
            if conf.project.name in ['mms', 'meta-driver']:
                if conf.project.name == 'mms' and 'edition' in conf.project:
                    if conf.project.edition == 'saas':
                        o = []
                    o.append('current')
            elif conf.build.system.branched is True:
                o.append('manual')
        else:
            if conf.project.name == 'mms' and 'edition' in conf.project:
                if conf.project.edition == 'hosted':
                    o.append(branch)

        return '/'.join(o)


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

    if 'branched' not in conf.build.system:
        if conf.project.name in ['manual', 'mms', 'meta-driver']:
            conf.build.system.branched = True
        else:
            conf.build.system.branched = False

    conf.git.branches.current = get_branch()
    conf.git.commit = get_commit()
    conf.project.basepath = get_manual_path(conf)

    conf.build.paths.update(render_paths('dict', conf))

    return conf

def get_versions(conf=None):
    if conf is None:
        conf = load_conf()

    o = []

    for version in conf.version.published:
        if version in ['current', 'master', 'upcoming']:
            if version == 'upcoming':
                version = str(conf.version.upcoming)
                path_name = 'master' # we may want to change this later.
            else:
                path_name = version
        else:
            path_name = 'v' + version


        if conf.project.name == 'mms':
            if version == conf.version.stable:
                path_name = 'current'

            if path_name == 'master':
                path_name = 'current'

        else:
            if version == conf.version.stable:
                version += ' (current)'
                path_name = 'manual'
            elif version == conf.version.upcoming:
                version = conf.version.upcoming + ' (upcoming)'
                path_name = 'master'

        o.append( { 'v': path_name, 't': version } )

    return o

def output_yaml(fn, conf=None):
    if conf is None:
        conf = get_conf()

    o = {
            'branch': get_branch(),
            'commit': get_commit(),
            'manual_path': get_manual_path(conf),
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
    paths.buildarchive = os.path.join(paths.output, 'archive')

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
