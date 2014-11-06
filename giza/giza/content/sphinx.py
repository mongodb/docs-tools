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

import collections
import logging
import os.path
import pkg_resources
import re
import sys

from multiprocessing import cpu_count

logger = logging.getLogger('giza.content.sphinx')

from giza.core.app import BuildApp
from giza.tools.command import command
from giza.tools.files import safe_create_directory
from giza.tools.timing import Timer
from giza.config.helper import get_config_paths
from giza.content.links import create_manual_symlink, get_public_links
from giza.content.manpages import manpage_url_tasks
from giza.content.post.json_output import json_output_tasks
from giza.content.post.singlehtml import finalize_single_html_tasks
from giza.content.post.archives import man_tarball, html_tarball, get_tarball_name
from giza.content.post.gettext import gettext_tasks
from giza.content.post.slides import slide_tasks
from giza.content.post.latex import pdf_tasks
from giza.content.post.sites import (finalize_epub_build,
                                     finalize_dirhtml_build, error_pages)

#################### Config Resolution ####################

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

    return ' '.join([' '.join(['-t', i ])
                     for i in ret
                     if i is not None])

def get_sphinx_args(sconf, conf):
    o = []

    o.append(get_tags(sconf.builder, sconf))
    o.append('-q')

    o.append('-b {0}'.format(sconf.builder))

    if is_parallel_sphinx(pkg_resources.get_distribution("sphinx").version):
        if 'serial_sphinx' in conf.runstate:
            if conf.runstate.serial_sphinx == "publish":
                if ((len(conf.runstate.builder) >= 1 or 'publish' in conf.runstate.builder) or
                    len(conf.runstate.languages_to_build) >= 1 or
                    len(conf.runstate.editions_to_build) >= 1):
                    pass
                else:
                    o.append(' '.join( [ '-j', str(cpu_count()) ]))
            elif conf.runstate.serial_sphinx is False:
                o.append(' '.join( [ '-j', str(cpu_count()) ]))
            elif (isinstance(conf.runstate.serial_sphinx, (int, long, float)) and
                  conf.runstate.serial_sphinx > 1):
                o.append(' '.join(['-j', str(conf.runstate.serial_sphinx)]))
            else:
                pass
        elif len(conf.runstate.builder) >= cpu_count():
            pass
        else:
            o.append(' '.join( [ '-j', str(cpu_count()) ]))

    o.append(' '.join( [ '-c', conf.paths.projectroot ] ))

    if 'language' in sconf and sconf.language is not None:
        o.append("-D language='{0}'".format(sconf.language))

    return ' '.join(o)

#################### Output Management ####################

def output_sphinx_stream(out, conf):
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
            try:
                l = path_normalization(l.split(' ')[-1].strip()[1:-2], full_path, conf)
                printable[idx-1] += ' ' + l
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

    logger.info('sphinx builder has {0} lines of output, processed from {1}'.format(len(printable), len(out)))
    print_build_messages(printable)

def stable_deduplicate(lines):
    ## this should probably just use OrderedSet() in the future

    mapping = collections.OrderedDict()

    for idx, ln in enumerate(lines):
        mapping[ln] = idx

    if sys.version_info >= (3, 0):
        return [ ln for _, ln in mapping.keys() ]
    else:
        return mapping.keys()

def print_build_messages(messages):
    for l in ( l for l in messages if l is not None ):
        print(l)

def path_normalization(l, full_path, conf):
    if l.startswith('..'):
        l = os.path.sep.join([ el for el in l.split(os.path.sep)
                               if el != '..'])

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
    elif l.endswith('should look like "opt", "-opt args", "--opt args" or "/opt args" or "+opt args"'):
        return False
    elif l.endswith('should look like "-opt args", "--opt args" or "/opt args" or "+opt args"'):
        return False
    elif l.endswith('should look like "opt", "-opt args", "--opt args" or "/opt args"'):
        return False
    else:
        return True

def printer(string):
    logger.info(string)

#################### Builder Operation ####################

def run_sphinx(builder, sconf, conf):
    if safe_create_directory(sconf.build_output):
        logger.info('created directory "{1}" for sphinx builder {0}'.format(builder, sconf.build_output))

    if 'language' in sconf and sconf.language is not None:
        command('sphinx-intl build --language=' + sconf.language)
        logger.info('compiled all PO files for translated build.')

    logger.info('starting sphinx build {0}'.format(builder))

    cmd = 'sphinx-build {0} -d {1}/doctrees-{2} {3} {4}' # per-builder-doctree

    sphinx_cmd = cmd.format(get_sphinx_args(sconf, conf),
                            os.path.join(conf.paths.projectroot, conf.paths.branch_output),
                            os.path.basename(sconf.build_output),
                            os.path.join(conf.paths.projectroot, conf.paths.branch_source),
                            sconf.build_output)

    logger.debug(sphinx_cmd)
    with Timer("running sphinx build for: {0}, {1}, {2}".format(builder, sconf.language, sconf.edition)):
        out = command(sphinx_cmd, capture=True, ignore=True)

    # out = sphinx_native_worker(sphinx_cmd)
    logger.info('completed sphinx build {0}'.format(builder))

    if True: # out.return_code == 0:
        logger.info('successfully completed {0} sphinx build'.format(builder))

        finalizer_app = BuildApp(conf)
        finalizer_app.root_app = False
        finalize_sphinx_build(sconf, conf, finalizer_app)
        with Timer("finalize sphinx {0} build".format(builder)):
            finalizer_app.run()
    else:
        logger.warning('the sphinx build {0} was not successful. not running finalize operation'.format(builder))

    output = '\n'.join([out.err, out.out])

    return out.return_code, output

#################### Application Logic ####################

def sphinx_tasks(sconf, conf, app):
    deps = [None] # always force builds until depchecking is fixed
    deps.extend(get_config_paths('sphinx_local', conf))
    deps.append(os.path.join(conf.paths.projectroot, conf.paths.source))
    deps.extend(os.path.join(conf.paths.projectroot, 'conf.py'))

    task = app.add('task')
    task.job = run_sphinx
    task.conf = conf
    task.args = [sconf.builder, sconf, conf]
    task.target = os.path.join(conf.paths.projectroot, conf.paths.branch_output, sconf.builder)
    task.dependency = deps
    task.description = 'building {0} with sphinx'.format(sconf.builder)

def finalize_sphinx_build(sconf, conf, app):
    target = sconf.builder
    logger.info('starting to finalize the Sphinx build {0}'.format(target))

    if target == 'html':
        app.pool = 'serial'
        task = app.add('task')
        task.job = html_tarball
        task.target = [get_tarball_name('html', conf),
                       get_tarball_name('link-html', conf)]
        task.args = [sconf.name, conf]
        task.description = "creating tarball for html archive"
    elif target == 'dirhtml':
        app.pool = 'thread'
        for job in (finalize_dirhtml_build, error_pages):
            task = app.add('task')
            task.job = job
            task.target = os.path.join(conf.paths.projectroot, conf.paths.public_site_output)
            task.dependency = None
            task.args = [sconf, conf]

        if conf.system.branched is True and conf.git.branches.current == 'master':
            link_task = app.add('task')
            link_task.job = create_manual_symlink
            link_task.target = [ t[0] for t in get_public_links(conf) ]
            link_task.dependency = get_config_paths('integration',conf)
            link_task.dependency.append(os.path.join(conf.paths.projectroot,
                                                     conf.paths.public_site_output))
            link_task.args = [conf]
            link_task.description = "create the 'manual' symlink"
    elif target == 'epub':
        app.pool = 'serial'
        task = app.add('task')
        task.job = finalize_epub_build
        task.args = (target, conf)
        task.description = 'finalizing epub build'
    elif target == 'man':
        app.pool = 'thread'
        manpage_url_tasks(target, conf, app)
        task = app.add('task')
        task.job = man_tarball
        task.target = [get_tarball_name('man', conf),
                       get_tarball_name('link-man', conf)]
        task.args = [target, conf]
        task.description = "creating tarball for manpages"
    elif target == 'slides':
        app.pool = 'thread'
        slide_tasks(sconf, conf, app)
    elif target == 'json':
        app.pool = 'thread'
        json_output_tasks(conf, app)
    elif target == 'singlehtml':
        app.pool = 'thread'
        finalize_single_html_tasks(target, conf, app)
    elif target == 'latex':
        app.pool = 'thread'
        pdf_tasks(sconf, conf, app)
    elif target == 'gettext':
        app.pool = 'thread'
        gettext_tasks(conf, app)
    elif target == 'linkcheck':
        app.pool = 'serial'
        task = app.add('task')
        task.job = printer
        task.target = os.path.join(conf.paths.projectroot,
                                   conf.paths.branch_output, builder, 'output.txt')
        task.args = '{0}: See {1}/{0}/output.txt for output.'.format(builder, conf.paths.branch_output)
