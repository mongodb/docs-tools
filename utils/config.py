import os.path

import yaml

try:
    from utils.structures import BuildConfiguration, AttributeDict
    from utils.git import get_branch, get_commit, get_file_from_branch
    from utils.project import (discover_config_file, get_manual_path, is_processed,
                               edition_setup, mangle_paths,
                               mangle_configuration)
    from utils.shell import CommandError
except ImportError:
    from structures import BuildConfiguration, AttributeDict
    from git import get_branch, get_commit, get_file_from_branch
    from project import (discover_config_file, get_manual_path, is_processed,
                         edition_setup, mangle_paths,
                         mangle_configuration)
    from shell import CommandError

def lazy_conf(conf=None):
    if conf is None:
        conf = get_conf()

    return conf

def get_conf_file(file, directory=None):
    if directory is None:
        conf = get_conf()
        directory = conf.paths.builddata

    conf_file = os.path.split(file)[1].rsplit('.', 1)[0] + '.yaml'

    return os.path.join(directory, conf_file)

def get_conf():
    project_root_dir, conf_file, conf = discover_config_file()

    conf = schema_migration_0(conf)

    conf.paths.projectroot = project_root_dir
    conf.system.conf_file = conf_file

    if os.path.exists('/etc/arch-release'):
        conf.system.python = 'python2'
    else:
        conf.system.python = 'python'

    conf.system.processed = AttributeDict()
    conf.system.processed.paths = False
    conf.system.processed.edition = False
    conf.system.processed.project_paths = False
    conf.system.processed.project_conf = False
    conf.system.processed.versions = False

    conf = render_versions(conf)
    conf = mangle_configuration(conf)

    conf.git.branches.current = get_branch()
    conf.git.commit = get_commit()
    conf.project.basepath = get_manual_path(conf)

    conf = render_paths(conf)
    conf = mangle_paths(conf)

    conf.system.dependency_cache = os.path.join(conf.paths.projectroot,
                                                conf.paths.branch_output,
                                                'dependencies.json')

    return conf

def render_versions(conf=None):
    if is_processed('versions', conf):
        return conf
    else:
        conf = lazy_conf(conf)

        version_config_file = os.path.join(conf.paths.builddata,
                                           'published_branches.yaml')

        try:
            vconf_data = get_file_from_branch(version_config_file, 'master')
        except CommandError:
            return conf

        vconf = AttributeDict(yaml.load(vconf_data))

        conf.version.update(vconf.version)

        if 'branches' not in conf.git:
            conf.git.branches = AttributeDict()

        conf.git.branches.update(vconf.git.branches)

        conf.system.processed.versions = True

        return conf

def render_paths(conf=None, language=None):
    if is_processed('paths', conf):
        return conf
    else:
        conf = lazy_conf(conf)

        if language is None:
            public_path = 'public'
        else:
            public_path = os.path.join('public', language)

        conf.paths.public = os.path.join(conf.paths.output, public_path)
        conf.paths.branch_output = os.path.join(conf.paths.output, get_branch())
        conf.paths.branch_source = os.path.join(conf.paths.branch_output, 'source')
        conf.paths.branch_staging = os.path.join(conf.paths.public, get_branch())
        conf.paths.buildarchive = os.path.join(conf.paths.output, 'archive')

        conf.system.processed.paths = True
        return conf

#### Configuration Object Schema Migration Code ####

def schema_migration_0(conf):
    if 'paths' not in conf:
        conf.paths = AttributeDict(conf.build.paths)
        del conf.build['paths']

    if 'system' not in conf:
        conf.system = AttributeDict()
        conf.system.make = AttributeDict()
        conf.system.make.generated = conf.build.system.files
        conf.system.make.static = conf.build.system.static
        del conf.build.system['files']
        del conf.build.system['static']
        conf.system.update(conf.build.system)

        del conf.build['system']

    if 'build' in conf:
        del conf['build']

    return conf
