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

"""
This module creates captures hashes of all content in the repository and stores
this information between builds, so that the build system has the ability to
test which files change in between builds, so that ``giza`` does not need to
rely on ``mtime``, which can change following branch operations in git.

Furthermore the tasks created as part of the build here use the implicit
relationship between source files determined by :mod:`giza.includes` in
combination with this cache of file hashes to ensure that Sphinx does not skip
building files.
"""

import datetime
import json
import logging
import os

import giza.libgiza.task

from giza.includes import include_files
from giza.tools.files import expand_tree, safe_create_directory, md5_file
from giza.tools.timing import Timer

logger = logging.getLogger('giza.content.dependencies')

# Update File Hashes


def dump_file_hashes(conf):
    output = conf.system.dependency_cache

    o = {'time': datetime.datetime.utcnow().strftime("%s"),
         'files': {}}

    files = expand_tree(os.path.join(conf.paths.projectroot, conf.paths.branch_source), None)

    fmap = o['files']

    for fn in files:
        if os.path.exists(fn):
            fmap[fn] = md5_file(fn)

    safe_create_directory(os.path.dirname(output))

    with open(output, 'w') as f:
        json.dump(o, f)

    logger.debug('wrote dependency cache to: {0}'.format(output))

# Update Dependencies


def _refresh_deps(graph, dep_map, conf):
    warned = set()
    count = 0

    # For each file in the source tree, bump the timestamp of all files that
    # include it, if the file changed since the last build.

    for file, dependents in graph.items():
        if check_hashed_dependency(file, dep_map, conf) is True:
            core_file = normalize_dep_path(file, conf, False)
            norm_file = normalize_dep_path(file, conf, True)

            if os.path.isfile(norm_file) and not os.path.isfile(core_file):
                # these are generated files in the build/<branch>/source. No
                # need to touch these files.
                continue
            for dep in [normalize_dep_path(dep, conf, branch=True) for dep in dependents]:
                if not os.path.exists(core_file):
                    # this file doesn't exist in the source. Sphinx will
                    # warn about this file later (though the output silently
                    # ignores the unavailable content.)

                    if core_file in warned:
                        continue
                    else:
                        warned.add(core_file)
                        logger.warning('included file does not exist: ' + core_file)
                elif os.path.exists(dep):
                    logger.debug('updating timestamp of "{0}" because of "{1}"'.format(dep, file))
                    os.utime(dep, None)
                    count += 1

    logger.debug('bumped timestamps for {0} files'.format(count))


def refresh_deps(conf):
    with Timer('resolve dependency graph'):
        # resolve a map of the source files to the files they depend on
        # (i.e. the ones that they include).
        graph = include_files(conf=conf)

        # load, if possible, a mappping of all source files with hashes from the
        # last build.
        if not os.path.exists(conf.system.dependency_cache):
            dep_map = None
        else:
            with open(conf.system.dependency_cache, 'r') as f:
                try:
                    dep_cache = json.load(f)
                    dep_map = dep_cache['files']
                except ValueError:
                    dep_map = None
                    m = 'no stored dependency information, will rebuild more things than necessary.'
                    logger.warning(m)

    with Timer('dependency updates'):
        _refresh_deps(graph, dep_map, conf)

# In previous versions, giza loaded the dep_map in the main thread, and then
# passed the checks and update to a worker pool, but the pool took ~40 seconds
# on a large resource, and doing the entire operation serially in a thread takes
# ~1 second.


def refresh_dependency_tasks(conf):
    return [giza.libgiza.task.Task(job=refresh_deps,
                                   args=[conf],
                                   target=None,
                                   dependency=conf.system.dependency_cache,
                                   description="check and touch files affected by dependency changes")]


def dump_file_hash_tasks(conf):
    return [giza.libgiza.task.Task(job=dump_file_hashes,
                                   args=[conf],
                                   target=conf.system.dependency_cache,
                                   dependency=os.path.join(conf.paths.projectroot,
                                                           conf.paths.branch_source),
                                   description="writing dependency cache to a file for the next build")]

# Hashed Dependency Checking


def normalize_dep_path(fn, conf, branch):
    """
    Given a filename (typically, absolute with regards to the ``source``
    directory), the configuration object, the ``branch`` boolean, returns a
    fully qualified path of a source file.

    When ``branch`` is ``False``, that's in the actual ``source/``
    directory. When ``branch`` is ``True``, that's the proxy-source directory in
    ``build/<branch>``.
    """

    fn = fn.rstrip()
    if not fn.startswith(conf.paths.projectroot):
        if fn.startswith(conf.paths.branch_source) or fn.startswith(conf.paths.source):
            fn = os.path.join(conf.paths.projectroot, fn)
        elif fn.startswith('/'):
            if branch is False:
                fn = os.path.join(conf.paths.projectroot,
                                  conf.paths.source,
                                  fn[1:])
            else:
                fn = os.path.join(conf.paths.projectroot,
                                  conf.paths.branch_source,
                                  fn[1:])

    return fn


def check_hashed_dependency(fn, dep_map, conf):
    """
    :return: ``True`` when any of the files that include ``fn`` have changed since
        the generation of the the ``dep_map``. Always returns ``True`` if
        ``dep_map`` is ``None`` (i.e. if this is the first build.)
    """
    # logger.info('checking dependency for: ' + fan)

    fn = normalize_dep_path(fn, conf, branch=False)

    if dep_map is None:
        return True
    elif not os.path.exists(fn):
        return True
    elif fn in dep_map:
        if dep_map[fn] != md5_file(fn):
            return True
        else:
            return False
    else:
        return False
