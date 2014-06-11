import os
import json
import logging

from giza.tools.jobs.dependency import check_hashed_dependency
from giza.content.includes import include_files

logger = logging.getLogger(os.path.basename(__file__))

########## Update Dependencies ##########

def dep_refresh_worker(target, deps, dep_map, conf):
    if check_hashed_dependency(target, deps, dep_map, conf) is True:
        target = os.path.join(conf.paths.projectroot,
                              conf.paths.branch_source,
                              target[1:])

        update_dependency(target)
        logger.debug('updated timestamp of {0} because of changed dependencies'.format(target))

def update_dependency(fn):
    if os.path.exists(fn):
        os.utime(fn, None)

def refresh_dependency_tasks(conf, app):
    graph = include_files(conf=conf)

    if not os.path.exists(conf.system.dependency_cache):
        dep_map = None
    else:
        with open(conf.system.dependency_cache, 'r') as f:
            try:
                dep_cache = json.load(f)
                dep_map = dep_cache['files']
            except ValueError:
                dep_map = None

    for target, deps in graph.items():
        t = app.add('task')
        t.job = dep_refresh_worker
        t.args = [target, deps, dep_map, conf]
        t.description = 'checking dependencies for changes and bumping mtime for {0}'.format(target)

        logger.debug('adding dep check task for ' + target)
