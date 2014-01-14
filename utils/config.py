import os

try:
    from utils.structures import BuildConfiguration, AttributeDict
    from utils.git import get_branch, get_commit
    from utils.project import (tmp_conf_file_path_migration, get_manual_path, is_processed,
                               tmp_conf_schema_migration, edition_setup,
                               project_specific_path_mangling,
                               project_specific_conf_mangling)
except ImportError:
    from structures import BuildConfiguration, AttributeDict
    from git import get_branch, get_commit
    from project import (tmp_conf_file_path_migration, get_manual_path, is_processed,
                               tmp_conf_schema_migration, edition_setup,
                               project_specific_path_mangling,
                               project_specific_conf_mangling)

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
    project_root_dir, conf_file, conf = tmp_conf_file_path_migration()

    conf = tmp_conf_schema_migration(conf)

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

    conf = project_specific_conf_mangling(conf)

    conf.git.branches.current = get_branch()
    conf.git.commit = get_commit()
    conf.project.basepath = get_manual_path(conf)
    conf.paths.update(render_paths(conf))

    conf = project_specific_path_mangling(conf)

    conf.system.dependency_cache = os.path.join(conf.paths.projectroot,
                                                conf.paths.branch_output,
                                                'dependencies.json')

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
        return conf.paths
