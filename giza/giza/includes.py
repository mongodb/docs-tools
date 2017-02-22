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

import os
import re
import itertools
import operator
import subprocess
import shlex

import yaml

from giza.tools.files import expand_tree


def include_files(conf, files=None):
    if files is not None:
        return files
    else:
        source_dir = os.path.join(conf.paths.projectroot, conf.paths.source)
        cmd = shlex.split('grep -R ".. include:: /" {0}'.format(source_dir))

        with open(os.devnull, 'w') as null:
            try:
                grep = subprocess.check_output(args=cmd, stderr=null)
            except subprocess.CalledProcessError as e:
                grep = e.output

        rx = re.compile(source_dir + r'(.*):.*\.\. include:: (.*)')

        s = [m.groups()
             for m in [rx.match(d)
                       for d in grep.split('\n')]
             if m is not None
             ]

        def tuple_sort(k):
            return k[1]
        s.sort(key=tuple_sort)

        files = dict()

        for i in itertools.groupby(s, operator.itemgetter(1)):
            files[i[0]] = set()
            for src in i[1]:
                if not src[0].endswith('~') and not src[0].endswith('overview.rst'):
                    files[i[0]].add(src[0])
            files[i[0]] = list(files[i[0]])
            files[i[0]].sort()

        for k, v in generated_includes(conf).items():
            if k in files:
                files[k].extend(v)
            else:
                files[k] = v

        return files


def included_once(conf, inc_files=None):
    results = []
    for file, includes in include_files(conf=conf, files=inc_files).items():
        if len(includes) == 1:
            results.append(file)
    return results


def included_recusively(conf, inc_files=None):
    files = include_files(conf=conf, files=inc_files)
    included_files = set(files.keys())

    results = {}
    for inc, srcs in files.items():
        for src in srcs:
            if src in included_files:
                results[inc] = srcs
                break

    return results


def includes_masked(mask, conf, inc_files=None):
    files = include_files(conf=conf, files=inc_files)

    results = {}
    try:
        m = mask + '.rst'
        results[m] = files[m]
    except (ValueError, KeyError):
        for pair in files.items():
            if pair[0].startswith(mask):
                results[pair[0]] = pair[1]

    return results


def generated_includes(conf):
    step_files = []
    mapping = {}

    content_prefixes = []
    for _, prefixes in conf.system.content.content_prefixes:
        content_prefixes.extend(prefixes)

    for fn in expand_tree(os.path.join(conf.paths.includes), input_extension='yaml'):
        base = os.path.basename(fn)

        # example/toc-specs files, for the purpose of this have the same
        # structure as steps, so we can just use that
        for prefix in content_prefixes:
            if base.startswith(prefix):
                step_files.append(fn)
                break

    maskl = len(conf.paths.source)
    path_prefix = conf.paths.includes[len(conf.paths.source):]

    for step_def in step_files:
        deps = []

        with open(step_def, 'r') as f:
            data = yaml.safe_load_all(f)

            for step in data:
                if 'source' in step:
                    deps.append(step['source']['file'])

        if len(deps) != 0:
            deps = [os.path.join(path_prefix, i) for i in deps]

            mapping[step_def[maskl:]] = deps

    return mapping


def include_files_unused(conf, inc_files=None):
    inc_files = [fn[6:] for fn in expand_tree(os.path.join(conf.paths.includes), None)]
    keys = set(include_files(conf=conf).keys())

    results = []
    for fn in inc_files:
        if fn.endswith('yaml') or fn.endswith('~'):
            continue
        if fn not in keys:
            results.append(fn)

    return results


def changed_includes(conf):
    from pygit2 import Repository, GIT_STATUS_CURRENT, GIT_STATUS_IGNORED

    repo_path = conf.paths.projectroot

    r = Repository(repo_path)

    changed = []
    for path, flag in r.status().items():
        if flag not in [GIT_STATUS_CURRENT, GIT_STATUS_IGNORED]:
            if path.startswith('source/'):
                if path.endswith('.txt') or path.endswith('.rst'):
                    changed.append(path[6:])

    changed_report = []

    for fn in include_files(conf):
        if fn in changed:
            changed_report.append(fn)

    return changed_report
