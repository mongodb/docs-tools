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

from libgiza.task import Task
from giza.tools.command import command
from giza.tools.files import safe_create_directory
from giza.tools.timing import Timer
from giza.config.helper import get_config_paths
from giza.content.links import create_manual_symlink, get_public_links
from giza.content.post.json_output import json_output_tasks
from giza.content.post.singlehtml import finalize_single_html_tasks
from giza.content.post.archives import man_tarball, html_tarball, get_tarball_name
from giza.content.post.manpages import manpage_url_tasks
from giza.content.post.gettext import gettext_tasks
from giza.content.post.slides import slide_tasks
from giza.content.post.latex import pdf_tasks
from giza.content.post.sites import (finalize_epub_build,
                                     finalize_dirhtml_build, error_pages)

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
            logger.info('running with serial sphinx processes')
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
    out = [o for o in out.split('\n') if o != '']

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
        print(l)


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


def printer(string):
    logger.info(string)

# Builder Operation


def run_sphinx(builder, sconf, conf):
    if safe_create_directory(sconf.fq_build_output):
        m = 'created directory "{1}" for sphinx builder {0}'
        logger.info(m.format(builder, sconf.fq_build_output))

    if 'language' in sconf and sconf.language is not None:
        command('sphinx-intl build --language=' + sconf.language)
        logger.info('compiled all PO files for translated build.')

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
        out = command(sphinx_cmd, capture=True, ignore=True)

    logger.info('completed {0} sphinx build ({1})'.format(builder, out.return_code))

    output = '\n'.join([out.err, out.out])

    return out.return_code, output

# Application Logic


def sphinx_tasks(sconf, conf):
    deps = [None]  # always force builds until depchecking is fixed
    deps.extend(get_config_paths('sphinx_local', conf))
    deps.append(os.path.join(conf.paths.projectroot, conf.paths.source))
    deps.extend(os.path.join(conf.paths.projectroot, 'conf.py'))

    return Task(job=run_sphinx,
                args=(sconf.builder, sconf, conf),
                target=os.path.join(conf.paths.projectroot,
                                    conf.paths.branch_output,
                                    sconf.builder),
                dependency=deps,
                description='building {0} with sphinx'.format(sconf.builder))


def finalize_sphinx_build(sconf, conf):
    target = sconf.builder

    tasks = []
    if target == 'html' and not conf.runstate.fast:
        t = Task(job=html_tarball,
                 args=(sconf.name, conf),
                 target=[get_tarball_name('html', conf),
                         get_tarball_name('link-html', conf)],
                 dependency=None,
                 description="creating tarball for html archive")
        tasks.append(t)
    elif target == 'dirhtml' and not conf.runstate.fast:
        for job in (finalize_dirhtml_build, error_pages):
            t = Task(job=job,
                     args=(sconf, conf),
                     target=os.path.join(conf.paths.projectroot, conf.paths.public_site_output),
                     dependency=None)
            tasks.append(t)

        if conf.system.branched is True and conf.git.branches.current == 'master':
            deps = get_config_paths('integration', conf)
            deps.append(os.path.join(conf.paths.projectroot,
                                     conf.paths.public_site_output))

            t = Task(job=create_manual_symlink,
                     args=[conf],
                     target=[link[0] for link in get_public_links(conf)],
                     dependency=deps,
                     description='create symlinks')
            tasks.append(t)
    elif target == 'epub':
        t = Task(job=finalize_epub_build,
                 args=(target, conf),
                 description='finalizing epub build',
                 dependency=None,
                 target=True)
        tasks.append(t)
    elif target == 'man':
        t = Task(job=man_tarball,
                 args=(target, conf),
                 target=[get_tarball_name('man', conf),
                         get_tarball_name('link-man', conf)],
                 dependency=None,
                 description="creating tarball for manpages")

        tasks.extend(manpage_url_tasks(target, conf))
        tasks.append(('final', t))
    elif target == 'slides' and not conf.runstate.fast:
        tasks.extend(slide_tasks(sconf, conf))
    elif target == 'json':
        json_tasks, transfer_op = json_output_tasks(conf)
        tasks.extend(json_tasks)
        tasks.append(('final', transfer_op))  # this is less than ideal
    elif target == 'singlehtml':
        tasks.extend(finalize_single_html_tasks(target, conf))
    elif target == 'latex':
        tasks.extend(pdf_tasks(sconf, conf))
    elif target == 'gettext':
        tasks.extend(gettext_tasks(conf))
    elif target == 'linkcheck':
        msg_str = '{0}: See {1}/{0}/output.txt for output.'
        t = Task(job=printer,
                 args=[msg_str.format(target, conf.paths.branch_output)],
                 target=os.path.join(conf.paths.projectroot,
                                     conf.paths.branch_output, target, 'output.txt'),
                 dependency=None)
        tasks.append(t)

    logger.info('adding {0} finalizing tasks for {1} build'.format(len(tasks), target))
    return tasks
