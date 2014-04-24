import os.path
import yaml
import json
import logging

logger = logging.getLogger(os.path.basename(__file__))

try:
    import utils.bootstrap as bootstrap
    from utils.structures import AttributeDict, BuildConfiguration
    from utils.git import get_branch, get_commit, get_file_from_branch
    from utils.project import (discover_config_file, get_manual_path, is_processed, mangle_paths,
                               mangle_configuration)
    from utils.shell import CommandError, command
    from utils.serialization import ingest_yaml
except ImportError:
    import bootstrap
    from serialization import ingest_yaml
    from structures import AttributeDict, BuildConfiguration
    from git import get_branch, get_commit, get_file_from_branch
    from project import (discover_config_file, get_manual_path, is_processed, mangle_paths,
                         mangle_configuration)
    from shell import CommandError, command

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

def crawl_up_tree(path, base_len=-1):
    path_parts = os.path.abspath(path).split(os.path.sep)

    head = path_parts[:-base_len]
    tail = os.path.join(path_parts[-base_len:])

    for i in range(len(head), -1, -1):
        if path_parts[0] == '':
            cur_path = ['/']
        else:
            cur_path = []

        cur_path.extend(head[:i])
        cur_path.extend(tail)
        cur_path = os.path.join(*cur_path)

        if os.path.exists(cur_path):
            return cur_path

    return path

def safe_bootstrap(conf):
    conf_path = os.path.join(conf.paths.projectroot, conf.system.conf_file)
    build_tools_path = os.path.join(conf.paths.projectroot, conf.paths.buildsystem)

    bootstrap.fabric(build_tools_path, conf_path)
    bootstrap.config(build_tools_path, conf_path)
    bootstrap.utils(build_tools_path, conf_path)

    conf = get_conf()
    conf.system.processed.bootstrap = True
    logger.info('automatically ran safe tools bootstrapping procedures.')

    return conf

def get_conf():
    project_root_dir, conf_file, conf = discover_config_file()

    conf = schema_migration_0(conf)

    conf_file = crawl_up_tree(conf_file, 2)
    conf.paths.projectroot = os.path.abspath(os.path.join(os.path.dirname(conf_file), '..'))
    conf.system.conf_file = conf_file

    if os.path.exists('/etc/arch-release'):
        conf.system.python = 'python2'
    else:
        conf.system.python = 'python'

    conf.system.processed = AttributeDict()
    conf.system.processed.paths = False
    conf.system.processed.bootstrap = False
    conf.system.processed.edition = False
    conf.system.processed.project_paths = False
    conf.system.processed.project_conf = False
    conf.system.processed.versions = False
    conf.system.processed.assets = False
    conf.system.processed.git_info = False
    conf.system.processed.cached = False

    conf_artifact_project = os.path.realpath(os.path.join(conf.paths.buildsystem,
                                                   'config')).split(os.path.sep)[-2]

    if not conf.paths.projectroot.endswith(conf_artifact_project):
        return safe_bootstrap(conf)

    # order matters here:
    conf = mangle_configuration(conf)
    conf = render_git_info(conf)
    conf = render_versions(conf)
    conf = render_assets(conf)

    conf = render_paths(conf)
    conf = mangle_paths(conf)
    conf = render_cache(conf)
    conf = render_deploy_info(conf)

    return conf

def render_cache(conf):
    if is_processed('cached', conf):
        return conf
    else:
        conf.system.dependency_cache = os.path.join(conf.paths.projectroot,
                                                    conf.paths.branch_output,
                                                    'dependencies.json')

        conf_cache_dir = os.path.join(conf.paths.projectroot, conf.paths.branch_output)
        conf_cache = os.path.join(conf_cache_dir, 'conf-cache.json')

        if not os.path.exists(conf_cache_dir):
            os.makedirs(conf_cache_dir)

        with open(conf_cache, 'w') as f:
            json.dump(conf, f)

        conf.system.processed.cached = True
        return conf

def render_git_info(conf):
    if is_processed('git_info', conf):
        return conf
    else:
        if 'branches' not in conf.git:
            conf.git.branches = AttributeDict()
        conf.git.branches.current = get_branch()
        conf.git.commit = get_commit()
        conf.project.basepath = get_manual_path(conf)
        conf.system.processed.git_info = True

        return conf

def render_assets(conf):
    if is_processed('assets', conf):
        return conf
    else:
        if not isinstance(conf.assets, list):
            conf.assets = [ conf.assets ]

        conf.system.processed.assets = True
        return conf

def render_versions(conf=None):
    if is_processed('versions', conf):
        return conf
    else:
        conf = lazy_conf(conf)

        version_config_file = os.path.join(conf.paths.builddata,
                                           'published_branches.yaml')

        if conf.git.branches.current == 'master'and not os.path.exists(version_config_file):
            return conf

        try:
            vconf_data = get_file_from_branch(version_config_file, 'master')
        except CommandError:
            setup_config_remote('master', conf)
            vconf_data = get_file_from_branch(version_config_file, 'master')
        except CommandError:
            return conf

        vconf = AttributeDict(yaml.load(vconf_data))
        conf.version.update(vconf.version)
        conf.git.branches.update(vconf.git.branches)
        conf.system.processed.versions = True

        return conf

def setup_config_remote(branch_name, conf):
    remotes = command('git remote', capture=True).out.split('\n')

    if 'config-upstream' not in remotes:
        if conf.git.remote.upstream.startswith('10gen'):
            git_url = 'git@github.com:'
        else:
            git_url = 'git://github.com/'

        command('git remote add config-upstream {0}{1}.git'.format(git_url, conf.git.remote.upstream))

        command('git fetch config-upstream')

        if branch_name not in command('git branch', capture=True).out.split('\n'):
            command('git branch {0} config-upstream/{0}'.format(branch_name))

def render_deploy_info(conf):
    if is_processed('deploy', conf):
        return conf
    else:
        deploy_conf_file = os.path.join(conf.paths.global_config, 'deploy.yaml')

        conf.deploy = BuildConfiguration(deploy_conf_file)
        conf.system.processed.deploy = True

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
        conf.paths.global_config = os.path.join(conf.paths.buildsystem, 'data')

        conf.system.processed.paths = True
        return conf

def get_sphinx_builders(conf=None):
    conf = lazy_conf(conf)

    path = os.path.join(conf.paths.builddata, 'sphinx.yaml')

    sconf = ingest_yaml(path)

    if 'builders' in sconf:
        return sconf['builders']
    else:
        for i in ['prerequisites', 'generated-source']:
            if i in sconf:
                del sconf[i]
        return sconf.keys()

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

    if 'branches' not in conf.git:
        conf.git.branches = AttributeDict()

    return conf
