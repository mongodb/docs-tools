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

    sconf = ingest_yaml(path)

    if 'builders' in sconf:
        return sconf['builders']
    else:
        for i in ['prerequisites', 'generated-source']:
            if i in sconf:
                del sconf[i]
        return sconf.keys()

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
    conf_file_name = 'docs_meta.yaml'

    try:
        project_root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
        conf_file_path = os.path.join(project_root_dir, 'bin')
        conf = BuildConfiguration(filename=conf_file_name,directory=conf_file_path)
    except IOError:
        project_root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
        conf_file_path = os.path.join(project_root_dir, 'bin')
        conf = BuildConfiguration(filename=conf_file_name, directory=conf_file_path)

    conf.build.paths.projectroot = project_root_dir
    conf.build.system.conf_file = os.path.join(conf_file_path, conf_file_name)

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

    current_branch = get_branch()
    if current_branch not in conf.git.branches.published:
        current_version_index = 0
    else:
        current_version_index = conf.git.branches.published.index(current_branch)

    for idx, version in enumerate(conf.version.published):
        v = {}

        branch = conf.git.branches.published[idx]
        v['path'] = get_path(conf, branch)

        v['text'] = version
        if version == conf.version.stable:
            v['text'] += ' (current)'

        if version == conf.version.upcoming:
            v['text'] += ' (upcoming)'

        v['current'] = True if idx == current_version_index else False

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

def edition_setup(edition, conf):
    if 'editions' in conf.project and edition in conf.project.editions:
        conf.project.edition = edition

    if conf.project.name == 'mms':
        conf.build.paths.public_site_output = conf.build.paths.mms[edition]
        conf.build.paths.branch_source = '-'.join([os.path.join(conf.build.paths.output,
                                                                conf.git.branches.current,
                                                                conf.build.paths.source),
                                                   edition])

        if edition == 'saas':
            conf.project.basepath = 'help'
        elif edition == 'hosted':
            conf.project.tag = 'help-hosted'
            conf.project.basepath = get_manual_path(conf)

        return conf
    else:
        return conf

def render_paths(fn, conf=None, language=None):
    if conf is None:
        conf = load_conf()

    paths = conf.build.paths

    if language is None:
        public_path = 'public'
    else:
        public_path = os.path.join('public', language)

    paths.public = os.path.join(paths.output, public_path)
    paths.branch_output = os.path.join(paths.output, get_branch())
    paths.branch_source = os.path.join(paths.branch_output, 'source')
    paths.branch_staging = os.path.join(paths.public, get_branch())
    paths.buildarchive = os.path.join(paths.output, 'archive')

    public_site_output = {
        'manual': os.path.join(paths.output, public_path, get_branch()),
        'ecosystem': os.path.join(paths.output, public_path),
        'about': os.path.join(paths.output, public_path),
        'meta-driver': os.path.join(paths.output, public_path, get_branch()),
        'mms': paths.public,
    }

    try:
        paths.public_site_output = public_site_output[conf.project.name]
    except KeyError:
        paths.public_site_output = paths.public

    if conf.project.name == 'mms':
        conf.build.paths.mms = {
            'hosted': os.path.join(paths.output, public_path, 'hosted', get_branch()),
            'saas': os.path.join(paths.output, public_path, 'saas')
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
