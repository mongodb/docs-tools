# Copyright 2014 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import logging
import os

from giza.content.includes import include_files
from giza.core.task import check_hashed_dependency
from giza.tools.files import expand_tree, md5_file

logger = logging.getLogger('giza.content.dependencies')

########## Update File Hashes ##########

def dump_file_hashes(conf):
    output = conf.system.dependency_cache

    o = { 'conf': conf.dict(),
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

########## Update Dependencies ##########

def dep_refresh_worker(target, deps, dep_map, conf):
    if check_hashed_dependency(target, deps, dep_map, conf) is True:
        target = os.path.join(conf.paths.projectroot,
                              conf.paths.branch_source,
                              target[1:])

        update_dependency(target)

        logger.debug('updated timestamp of {0} because of changed dependencies: {1}'.format(target, ', '.join(deps)))

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
                logger.warning('no stored dependency information, will rebuild more things than necessary.')

    for target, deps in graph.items():
        t = app.add('task')
        t.job = dep_refresh_worker
        t.args = [target, deps, dep_map, conf]
        t.description = 'checking dependencies for changes and bumping mtime for {0}'.format(target)
        logger.debug('adding dep check task for ' + target)
