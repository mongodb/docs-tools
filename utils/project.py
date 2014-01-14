import itertools
import os

try:
    from utils.git import get_branch
    from utils.structures import BuildConfiguration, AttributeDict
except ImportError:
    from git import get_branch
    from structures import BuildConfiguration, AttributeDict

# duplicated from config.py to avoid circular import
def lazy_conf(conf=None):
    if conf is None:
        conf = get_conf()

    return conf

def is_processed(key, conf):
    if key in conf.system.processed and conf.system.processed[key] is True:
        return True
    else:
        return False

def project_specific_path_mangling(conf):
    if is_processed('project_paths', conf):
        return conf
    else:
        public_site_output = {
            'manual': os.path.join(conf.paths.public, get_branch()),
            'meta-driver': os.path.join(conf.paths.public, get_branch()),
            'ecosystem': conf.paths.public,
            'about': conf.paths.public,
            'mms': conf.paths.public,
        }

        try:
            conf.paths.public_site_output = public_site_output[conf.project.name]
        except KeyError:
            conf.paths.public_site_output = conf.paths.public

        if conf.project.name == 'mms':
            conf.paths.mms = AttributeDict({
                'hosted': os.path.join(conf.paths.public, 'hosted', get_branch()),
                'saas': os.path.join(conf.paths.public, 'saas')
            })

        conf.system.processed.project_paths = True
        return conf

def project_specific_conf_mangling(conf):
    if is_processed('project', conf) is True:
        return conf
    else:
        if 'branched' not in conf.system:
            if conf.project.name in ['manual', 'mms', 'meta-driver']:
                conf.system.branched = True
            else:
                conf.system.branched = False

        conf.system.processed.project_conf = True
        return conf

def edition_setup(edition, conf):
    if is_processed('edition', conf) is True:
        return conf
    else:
        if 'editions' in conf.project and edition in conf.project.editions:
            conf.project.edition = edition
        if conf.project.name == 'mms':
            conf.paths.public_site_output = conf.paths.mms[edition]
            conf.paths.branch_source = '-'.join([os.path.join(conf.paths.output,
                                                              conf.git.branches.current,
                                                              conf.paths.source), edition])
            if edition == 'saas':
                conf.project.basepath = 'help'
            elif edition == 'hosted':
                conf.project.tag = 'help-hosted'
                conf.project.basepath = get_manual_path(conf)

        conf.system.processed.edition = True
        return conf

def tmp_conf_file_path_migration():
    root_dirs = [ os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')),
                  os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')),
                  os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
                ]

    conf_dirs = [ 'bin', 'config' ]

    conf_file_names = ['build_conf.yaml', 'docs_meta.yaml']

    for project_root_dir in root_dirs:
        for path, filename in itertools.product(conf_dirs, conf_file_names):
            conf_file = os.path.join(path, filename)
            abs_conf_file = os.path.join(project_root_dir, conf_file)

            if not os.path.exists(abs_conf_file):
                continue
            else:
                conf = BuildConfiguration(abs_conf_file)
                return project_root_dir, conf_file, conf

def tmp_conf_schema_migration(conf):
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

def get_manual_path(conf=None):
    conf = lazy_conf(conf)

    if conf.system.branched is False:
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
        elif conf.system.branched is True:
            o.append('manual')
    else:
        if conf.project.name == 'mms' and 'edition' in conf.project:
            if conf.project.edition == 'hosted':
                o.append(branch)
        else:
            o.append(branch)

    return '/'.join(o)


def get_versions(conf=None):
    conf = lazy_conf(conf)

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
