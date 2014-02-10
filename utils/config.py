import os.path
import yaml

try:
    from utils.structures import AttributeDict
    from utils.git import get_branch, get_commit, get_file_from_branch
    from utils.project import (discover_config_file, get_manual_path, is_processed, mangle_paths,
                               mangle_configuration)
    from utils.shell import CommandError, command
    from utils.serialization import ingest_yaml
except ImportError:
    from serialization import ingest_yaml
    from structures import AttributeDict
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
    conf.system.processed.edition = False
    conf.system.processed.project_paths = False
    conf.system.processed.project_conf = False
    conf.system.processed.versions = False

    conf = mangle_configuration(conf)
    conf = render_versions(conf)

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

        if 'branches' not in conf.git:
            conf.git.branches = AttributeDict()

        version_config_file = os.path.join(conf.paths.builddata,
                                           'published_branches.yaml')

        try:
            vconf_data = get_file_from_branch(version_config_file, 'master')
        except CommandError:
            remotes = command('git remote', capture=True).out.split('\n')
            if 'config-upstream' in remotes:
                command('git remote add config-upstream git://github.com/{0}.git'.format(conf.git.remote.upstream))
            else:
                command('git fetch config-upstream')
                command('git branch master config-upstream/master')
                vconf_data = get_file_from_branch(version_config_file, 'master')
        except CommandError:
            return conf

        vconf = AttributeDict(yaml.load(vconf_data))

        conf.version.update(vconf.version)

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

    return conf
