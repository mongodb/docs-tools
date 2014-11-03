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

from giza.includes import include_files
from giza.core.task import check_hashed_dependency, normalize_dep_path
from giza.tools.files import expand_tree, md5_file
from giza.tools.timing import Timer

logger = logging.getLogger('giza.content.dependencies')

########## Update File Hashes ##########

def dump_file_hashes(conf):
    output = conf.system.dependency_cache

    o = { 'time': datetime.datetime.utcnow().strftime("%s"),
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

def _refresh_deps(graph, dep_map, conf):
    warned = set()
    for file, dependents in graph.items():
        if check_hashed_dependency(file, dep_map, conf) is True:
            core_file = normalize_dep_path(file, conf, False)
            norm_file = normalize_dep_path(file, conf, True)

            if os.path.isfile(norm_file) and not os.path.isfile(core_file):
                # these are generated files in the build/<branch>/source
                continue
            for dep in [ normalize_dep_path(dep, conf, branch=True) for dep in dependents]:
                if not os.path.exists(core_file):
                    if core_file in warned:
                        continue
                    else:
                        warned.add(core_file)
                        logger.warning('included file does not exist: ' + core_file)
                elif os.path.exists(dep):
                    logger.debug('updating timestamp of "{0}" because of "{1}"'.format(dep, file))
                    os.utime(dep, None)

    logger.info('refreshed all deps')

def refresh_deps(conf):
    with Timer('resolve dependency graph'):
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

    with Timer('dependency updates'):
        _refresh_deps(graph, dep_map, conf)

def refresh_dependency_tasks(conf, app):
    t = app.add('task')
    t.job = refresh_deps
    t.args = [conf]
    t.target = None
    t.dependency = conf.system.dependency_cache
    t.description = "check and touch files affected by dependency changes"

def dump_file_hash_tasks(conf, app):
    t = app.add('task')
    t.job = dump_file_hashes
    t.args = [conf]
    t.target = conf.system.dependency_cache
    t.dependency = os.path.join(conf.paths.projectroot, conf.paths.branch_source)
    t.description = "writing dependency cache"
