import os
import json

from utils.config import lazy_conf
from utils.jobs.runners import runner
from utils.jobs.dependency import check_hashed_dependency

from utils.contentlib.includes import include_files

########## Update Dependencies ##########

def update_dependency(fn):
    if os.path.exists(fn):
        os.utime(fn, None)

def refresh_dependency_jobs(conf):
    graph = include_files(conf=conf)

    if not os.path.exists(conf.system.dependency_cache):
        dep_map = None
    else:
        with open(conf.system.dependency_cache, 'r') as f:
            dep_cache = json.load(f)
            dep_map = dep_cache['files']

    for target, deps in graph.items():
        yield {
            'job': dep_refresh_worker,
            'args': [target, deps, dep_map, conf],
            'target': None,
            'dependency': None
        }

def dep_refresh_worker(target, deps, dep_map, conf):
    if check_hashed_dependency(target, deps, dep_map, conf) is True:
        target = os.path.join(conf.paths.projectroot,
                              conf.paths.branch_source,
                              target[1:])

        update_dependency(target)
        return 1
    else:
        return 0

def refresh_dependencies(conf=None):
    conf = lazy_conf(conf)

    results = runner(refresh_dependency_jobs(conf), pool=4, parallel='process', force=False)
    return sum(results)
