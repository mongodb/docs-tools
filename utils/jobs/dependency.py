import os
import json
import datetime
import logging

logger = logging.getLogger(os.path.basename(__file__))

try:
    from utils.files import md5_file, expand_tree
    from utils.config import lazy_conf
except ImportError:
    from ..files import md5_file, expand_tree
    from ..config import lazy_conf

############### Hashed Dependency Checking ###############

def check_hashed_dependency(target, dependency, dep_map, conf):
    def normalize_fn(fn):
        if not fn.startswith(conf.paths.projectroot):
            if fn.startswith(conf.paths.source):
                fn = os.path.join(conf.paths.projectroot, fn)
            if fn.startswith('/'):
                fn = os.path.join(conf.paths.projectroot,
                                  conf.paths.source,
                                  fn[1:])

        return fn

    def needs_rebuild(t, d):
        if dep_map is None:
            return check_dependency(t, d)
        elif d in dep_map:
            fn_hash = md5_file(d)
        else:
            return check_dependency(t, d)

        if dep_map[d] == fn_hash:
            return False
        else:
            return True

    if target is None or dependency is None:
        return True

    if isinstance(target, list):
        target = [ normalize_fn(t) for t in target ]
        for f in target:
            if not os.path.exists(f):
                return True
    else:
        target = normalize_fn(target)
        if not os.path.exists(target):
            return True

    if isinstance(dependency, list):
        dependency = [ normalize_fn(d) for d in dependency ]
        for dep in dependency:
            if needs_rebuild(target, dep) is True:
                return True
        return False
    else:
        dependency = normalize_fn(dependency)
        return needs_rebuild(target, dependency)

def dump_file_hashes(conf=None):
    conf = lazy_conf(conf)

    output = conf.system.dependency_cache

    o = { 'conf': conf,
          'time': datetime.datetime.utcnow().strftime("%s"),
          'files': { }
        }

    files = expand_tree(os.path.join(conf.paths.projectroot, conf.paths.source), None)

    fmap = o['files']

    for fn in files:
        if os.path.exists(fn):
            fmap[fn] = md5_file(fn)

    output_dir = os.path.dirname(output)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output, 'w') as f:
        json.dump(o, f)

    logger.info('wrote dependency cache to: {0}'.format(output))

############### Dependency Checking ###############

def check_three_way_dependency(target, source, dependency):
    if not os.path.exists(target):
        # if .json doesn't exist, rebuild
        return True
    else:
        dep_mtime = os.stat(dependency).st_mtime
        if os.stat(source).st_mtime > dep_mtime:
            # if <file>.txt is older than <file>.fjson,
            return True
        elif dep_mtime > os.stat(target).st_mtime:
            #if fjson is older than json
            return True
        else:
            return False

def check_dependency(target, dependency):
    if dependency is None:
        return True

    if isinstance(target, list):
        if len(target) == 1:
            target = target[0]
        else:
            return check_multi_dependency(target, dependency)

    if os.path.exists(target) is False:
        return True


    def needs_rebuild(targ_t, dep_f):
        if targ_t < os.path.getmtime(dep_f):
            return True
        else:
            return False

    target_time = os.path.getmtime(target)
    if isinstance(dependency, list):
        for dep in dependency:
            if needs_rebuild(target_time, dep) is True:
                return True
        return False
    else:
        return needs_rebuild(target_time, dependency)

def check_multi_dependency(target, dependency):
    for idx, t in enumerate(target):
        if check_dependency(t, dependency) is True:
            return True

    return False
