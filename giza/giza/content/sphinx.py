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

import re
import logging
import pkg_resources
import os.path
from multiprocessing import cpu_count

logger = logging.getLogger('giza.content.sphinx')

from giza.strings import timestamp

from giza.command import command
from giza.app import BuildApp
from giza.content.links import create_manual_symlink
from giza.content.manpages import manpage_url_tasks

from giza.content.post.archives import man_tarball, html_tarball
from giza.content.post.json_output import json_output_tasks
from giza.content.post.singlehtml import finalize_single_html_tasks
from giza.content.post.gettext import gettext_tasks
from giza.content.post.latex import pdf_tasks
from giza.content.post.sites import (finalize_epub_build,
                                     finalize_dirhtml_build, error_pages)

#################### Config Resolution ####################

def is_parallel_sphinx(version):
    return version >= '1.2'

def get_tags(target, sconf):
    ret = set()

    ret.add(target)
    ret.add(target.split('-')[0])

    if target.startswith('html') or target.startswith('dirhtml'):
        ret.add('website')
    else:
        ret.add('print')

    if 'edition' in sconf:
        ret.add(sconf.edition)

    return ' '.join([' '.join(['-t', i ])
                     for i in ret
                     if i is not None])

def get_sphinx_args(sconf, conf):
    o = []

    o.append(get_tags(sconf.builder, sconf))
    o.append('-q')

    o.append('-b {0}'.format(sconf.builder))

    if (is_parallel_sphinx(pkg_resources.get_distribution("sphinx").version) and
        'editions' not in sconf):
        o.append(' '.join( [ '-j', str(cpu_count() + 1) ]))

    o.append(' '.join( [ '-c', conf.paths.projectroot ] ))

    if 'language' in sconf:
        o.append("-D language='{0}'".format(sconf.language))

    return ' '.join(o)

#################### Output Management ####################

def output_sphinx_stream(out, conf):
    if isinstance(out, list):
        out = '\n'.join(out)

    out = [ o for o in out.split('\n') if o != '' ]

    full_path = os.path.join(conf.paths.projectroot, conf.paths.branch_output)

    regx = re.compile(r'(.*):[0-9]+: WARNING: duplicate object description of ".*", other instance in (.*)')

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
            l = path_normalization(l.split(' ')[-1].strip()[1:-2], full_path, conf)
            printable[idx-1] += ' ' + l
            l = None
        elif l.startswith('source/includes/generated/overview.rst'):
            continue
        elif l.startswith('source/meta/includes.txt'):
            continue

        printable.append(l)

    printable = list(set(printable))
    printable.sort()

    logger.info('sphinx builder has {0} lines of output, processed from {1}'.format(len(printable), len(out)))
    print_build_messages(printable)

def print_build_messages(messages):
    for l in ( l for l in messages if l is not None ):
        print(l)

def path_normalization(l, full_path, conf):
    if l.startswith(conf.paths.branch_output):
        l = l[len(conf.paths.branch_output)+1:]
    elif l.startswith(full_path):
        l = l[len(full_path)+1:]

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
    elif l.endswith('should look like "opt", "-opt args", "--opt args" or "/opt args"'):
        return False
    elif l.endswith('should look like "-opt args", "--opt args" or "/opt args"'):
        return False
    else:
        return True

def printer(string):
    logger.info(string)

#################### Builder Operation ####################

def run_sphinx(builder, sconf, conf):
    dirpath = os.path.join(conf.paths.branch_output, builder)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
        logger.info('created directories "{1}" for sphinx builder {0}'.format(builder, dirpath))

    logger.info('starting sphinx build {0} at {1}'.format(builder, timestamp()))

    cmd = 'sphinx-build {0} -d {1}/doctrees-{2} {3} {4}' # per-builder-doctreea

    sphinx_cmd = cmd.format(get_sphinx_args(sconf, conf),
                            os.path.join(conf.paths.projectroot, conf.paths.branch_output),
                            builder,
                            os.path.join(conf.paths.projectroot, conf.paths.branch_source),
                            os.path.join(conf.paths.projectroot, conf.paths.branch_output, builder))

    out = command(sphinx_cmd, capture=True, ignore=True)
    # out = sphinx_native_worker(sphinx_cmd)
    logger.info('completed sphinx build {0} at {1}'.format(builder, timestamp()))

    output = '\n'.join([out.err, out.out])

    if out.return_code == 0:
        logger.info('successfully completed {0} sphinx build at {1}'.format(builder, timestamp()))
    else:
        logger.warning('the sphinx build {0} was not successful. not running finalize operation'.format(builder))

    return out.return_code, sconf, conf, output

#################### Application Logic ####################

def sphinx_tasks(sconf, conf, app):
    task = app.add('task')
    task.job = run_sphinx
    task.conf = conf
    task.args = [sconf.builder, sconf, conf]
    task.description = 'building {0} with sphinx'.format(sconf.builder)

def finalize_sphinx_build(sconf, conf, app):
    target = sconf.builder

    logger.info('starting to finalize the Sphinx build {0}'.format(target))

    if target == 'linkcheck':
        task = app.add('task')
        task.job = printer
        task.args = '{0}: See {1}/{0}/output.txt for output.'.format(builder, conf.paths.branch_output)
    elif target == 'dirhtml':
        for job in (finalize_dirhtml_build, error_pages):
            task = app.add('task')
            task.job = job
            task.args = [target, conf]

        if conf.system.branched is True and conf.git.branches.current == 'master':
            link_task = app.add('task')
            link_task.job = create_manual_symlink
            link_task.args = [conf]
            link_task.description = "create the 'manual' symlink"
    elif target == 'epub':
        task = app.add('task')
        task.job = finalize_epub_build
        task.args = [target, conf]
        task.description = 'finalizing epub build'
    elif target == 'man':
        manpage_url_tasks(target, conf, app)
        task = app.add('task')
        task.job = man_tarball
        task.args = [target, conf]
        task.description = "creating tarball for manpages"
    elif target == 'html':
        task = app.add('task')
        task.job = html_tarball
        task.args = [target, conf]
        task.description = "creating tarball for html archive"
    elif target == 'json':
        json_output_tasks(conf, app)
    elif target == 'singlehtml':
        finalize_single_html_tasks(target, conf, app)
    elif target == 'latex':
        pdf_tasks(target, conf, app)
    elif target == 'gettext':
        gettext_tasks(conf, app)
