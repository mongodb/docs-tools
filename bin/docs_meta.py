#!/usr/bin/python

import datetime
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
        return get_path(conf, branch)

def get_path(conf, branch):
    o = []

    if conf.project.name in ['mms', 'meta-driver']:
        o.append(conf.project.tag)

    if branch == conf.git.branches.manual:
        if conf.project.name in ['mms', 'meta-driver']:
            if conf.project.name == 'mms' and 'edition' in conf.project:
                if conf.project.edition == 'saas':
                    pass
                o.append('current')
        elif conf.build.system.branched is True:
            o.append('manual')
    else:
        if conf.project.name == 'mms' and 'edition' in conf.project:
            if conf.project.edition == 'hosted':
                o.append(branch)
        else:
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
    conf.build.system.dependency_cache = os.path.join(conf.build.paths.projectroot,
                                                      conf.build.paths.branch_output,
                                                      'dependencies.json')

    return conf

def get_versions(conf=None):
    if conf is None:
        conf = get_conf()

    o = []

    current_version = conf.git.branches.published.index(get_branch())
    for idx, version in enumerate(conf.version.published):
        v = {}

        branch = conf.git.branches.published[idx]
        v['path'] = get_path(conf, branch)

        v['text'] = version
        if version == conf.version.stable:
            v['text'] += ' (current)'

        if version == conf.version.upcoming:
            v['text'] += ' (upcoming)'

        v['current'] = True if version == current_version else False

        o.append(v)

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
