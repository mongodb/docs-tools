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
Responsible for converting the Sphinx configuration stored by projects and used
by giza, into a ``sphinx-build`` invocation. See
:func:`giza.content.sphinx.run_sphinx` for the core of this operation.

:mod:`giza.content.sphinx` also contains:

- the error message processing, which normalizes references to paths,
  deduplicates log messages given multiple builds or multi-process Sphinx
  operation, and removes non-actionable messages. See
  :func:`giza.content.sphinx.output_sphinx_stream()`,
  :func:`giza.content.sphinx.is_msg_worth()` and
  :func:`giza.content.sphinx.path_normalization()`.

- the orchestration of all post-processing. See
  :func:`giza.content.sphinx.finalize_sphinx_build()`.
"""

import collections
import logging
import os.path
import pkg_resources
import re
import sys
import numbers
import subprocess
import shlex

from libgiza.task import Task
from giza.tools.files import safe_create_directory, expand_tree
from giza.tools.timing import Timer
from giza.tools.colorformatter import ColorFormatter

logger = logging.getLogger('giza.content.sphinx')

# Config Resolution


def is_parallel_sphinx(version):
    return version >= '1.2'


def get_tags(target, sconf):
    if 'tags' in sconf:
        ret = set(sconf.tags)
    else:
        ret = set()

    ret.add(target)
    ret.add(target.split('-')[0])

    if target.startswith('html') or target.startswith('dirhtml'):
        ret.add('website')
    else:
        ret.add('print')

    if 'edition' in sconf:
        ret.add(sconf.edition)

    return ' '.join([' '.join(['-t', i])
                     for i in ret
                     if i is not None])


def get_sphinx_args(sconf, conf):
    o = []

    o.append(get_tags(sconf.builder, sconf))
    o.append('-q')

    o.append('-b {0}'.format(sconf.builder))

    if is_parallel_sphinx(pkg_resources.get_distribution("sphinx").version):
        if 'serial_sphinx' in conf.runstate:
            m = 'running with serial sphinx processes ({0}.{1}.{2}.{3})'
            logger.info(m.format(sconf.builder, conf.project.name,
                                 conf.project.edition, conf.git.branches.current))
            if conf.runstate.serial_sphinx == "publish":
                if ((len(conf.runstate.builder) >= 1 or 'publish' in conf.runstate.builder) or
                        len(conf.runstate.languages_to_build) >= 1 or
                        len(conf.runstate.editions_to_build) >= 1):
                    pass
                else:
                    o.append(' '.join(['-j', str(conf.runstate.pool_size)]))
            elif conf.runstate.serial_sphinx is False:
                logger.info('running with parallelized sphinx processes')
                o.append(' '.join(['-j', str(conf.runstate.pool_size)]))
            elif (isinstance(conf.runstate.serial_sphinx, numbers.Number) and
                  conf.runstate.serial_sphinx > 1):
                logger.info('running with parallelized sphinx processes')
                o.append(' '.join(['-j', str(conf.runstate.serial_sphinx)]))
            else:
                pass
        elif len(conf.runstate.builder) >= conf.runstate.pool_size:
            logger.info('running with serail sphinx processes')
            pass
        else:
            logger.info('running with parallelized sphinx processes')
            o.append(' '.join(['-j', str(conf.runstate.pool_size)]))

    o.append(' '.join(['-c', conf.paths.projectroot]))

    if 'language' in sconf and sconf.language is not None:
        o.append("-D language='{0}'".format(sconf.language))

    return ' '.join(o)

# Output Management


def output_sphinx_stream(out, conf):
    full_path = os.path.join(conf.paths.projectroot, conf.paths.branch_output)

    regx = r'(.*):[0-9]+: WARNING: duplicate object description of ".*", other instance in (.*)'
    regx = re.compile(regx)

    printable = []
    for idx, l in enumerate(out):
        if is_msg_worthy(l) is False:
            printable.append(None)
            continue

        f1 = regx.match(l)
        if f1 is not None:
            g = f1.groups()

            if g[1].endswith(g[0]):
                printable.append(None)
                continue

        l = path_normalization(l, full_path, conf)

        if l.startswith('InputError: [Errno 2] No such file or directory'):
            try:
                l = path_normalization(l.split(' ')[-1].strip()[1:-2], full_path, conf)
                printable[idx - 1] += ' ' + l
                l = None
            except IndexError:
                logger.error("error processing log: {0}".format(l))
                continue
        elif l.startswith('source/includes/generated/overview.rst'):
            continue
        elif l.startswith('source/meta/includes.txt'):
            continue

        printable.append(l)

    printable = stable_deduplicate(printable)

    m = 'sphinx builder has {0} lines of output, processed from {1}'
    logger.info(m.format(len(printable), len(out)))
    print_build_messages(printable)


def stable_deduplicate(lines):
    # this should probably just use OrderedSet() in the future

    mapping = collections.OrderedDict()

    for idx, ln in enumerate(lines):
        mapping[ln] = idx

    if sys.version_info >= (3, 0):
        return [ln for _, ln in mapping.keys()]
    else:
        return mapping.keys()


def print_build_messages(messages):
    for l in (l for l in messages if l is not None):
        if 'WARNING: ' in l:
            logger.warn(l, extra={'lean': True})
        elif 'ERROR: ' in l or 'SEVERE: ' in l:
            logger.error(l, extra={'lean': True})
        else:
            logger.info(l, extra={'lean': True})


def path_normalization(l, full_path, conf):
    if l.startswith('..'):
        l = os.path.sep.join([el for el in l.split(os.path.sep)
                              if el != '..'])

    if l.startswith(conf.paths.branch_output):
        l = l[len(conf.paths.branch_output) + 1:]
    elif l.startswith(full_path):
        l = l[len(full_path) + 1:]

    if l.startswith('source'):
        l = os.path.sep.join(['source', l.split(os.path.sep, 1)[1]])

    return l


def is_msg_worthy(l):
    if l.startswith('WARNING: unknown mimetype'):
        return False
    elif len(l) == 0:
        return False
    elif l.startswith('WARNING: search index'):
        return False
    elif l.endswith('source/reference/sharding-commands.txt'):
        return False
    elif l.endswith('Duplicate ID: "cmdoption-h".'):
        return False
    elif l.endswith('"/opt args" or "+opt args"'):
        return False
    elif l.endswith('"--opt args" or "/opt args"'):
        return False
    elif 'nonlocal image URI found' in l:
        return False
    else:
        return True


# Builder Operation


def run_sphinx(builder, sconf, conf):
    if safe_create_directory(sconf.fq_build_output):
        m = 'created directory "{1}" for sphinx builder {0}'
        logger.info(m.format(builder, sconf.fq_build_output))

    if 'language' in sconf and sconf.language is not None:
        cmd_str = 'sphinx-intl build --language=' + sconf.language
        try:
            subprocess.check_call(shlex.split(cmd_str))
            logger.info('compiled all PO files for translated build.')
        except subprocess.CalledProcessError as e:
            logger.error('sphinx-intl encountered error: ' + str(e.returncode))
            logger.info(cmd_str)

    logger.info('starting sphinx build {0}'.format(builder))

    cmd = 'sphinx-build {0} -d {1}/doctrees-{2} {3} {4}'  # per-builder-doctree

    sphinx_cmd = cmd.format(get_sphinx_args(sconf, conf),
                            os.path.join(conf.paths.projectroot, conf.paths.branch_output),
                            sconf.build_output,
                            os.path.join(conf.paths.projectroot, conf.paths.branch_source),
                            sconf.fq_build_output)

    logger.debug(sphinx_cmd)
    m = "running sphinx build for: {0}, {1}, {2}"

    with Timer(m.format(builder, sconf.language, sconf.edition)):
        try:
            output = subprocess.check_output(shlex.split(sphinx_cmd), stderr=subprocess.STDOUT)
            return_code = 0
        except subprocess.CalledProcessError as e:
            output = e.output
            return_code = e.returncode
            logger.info(sphinx_cmd)
    try:
        os.utime(sconf.fq_build_output, None)
    except:
        pass

    m = 'completed {0} sphinx build for {1}.{2}.{3} ({4})'

    logger.info(m.format(builder, conf.project.name, conf.project.edition,
                         conf.git.branches.current, return_code))

    return return_code, output

# Application Logic


def sphinx_tasks(sconf, conf):
    # Projects that use the append functionality in extracts or similar content
    # generators will rebuild this task every time.

    deps = [os.path.join(conf.paths.projectroot, 'conf.py')]
    deps.extend(conf.system.files.get_configs('sphinx_local'))
    deps.extend(expand_tree(os.path.join(conf.paths.projectroot, conf.paths.branch_source), 'txt'))

    return Task(job=run_sphinx,
                args=(sconf.builder, sconf, conf),
                target=os.path.join(conf.paths.projectroot,
                                    conf.paths.branch_output,
                                    sconf.builder),
                dependency=deps,
                description='building {0} with sphinx'.format(sconf.builder))
