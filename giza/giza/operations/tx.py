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
Operations for managing and producing artifacts using the ``gettext`` builder,
``sphinx-intl``, and Transifex-based translation workflow.
"""

import logging
import os.path
import sys

import argh

logger = logging.getLogger('giza.operations.tx')

from giza.config.helper import fetch_config
from giza.config.sphinx_config import resolve_builder_path
from giza.core.app import BuildApp
from giza.tools.command import command
from giza.tools.files import FileLogger

from sphinx_intl.commands import update_txconfig_resources

#################### Helpers ####################

def tx_resources(conf):
    tx_conf = os.path.join(conf.paths.projectroot,
                           ".tx", 'config')

    with open(tx_conf, 'r') as f:
        resources = [ l.strip()[1:-1]
                      for l in f.readlines()
                      if l.startswith('[')][1:]

    return resources

def logged_command(verb, cmd):
    r = command(cmd, capture=True)
    logger.info('{0}ed {1}'.format(verb, cmd.split(' ')[-1]))

    return r.out

def check_for_orphaned_tx_files(conf):
    tx_conf = os.path.join(conf.paths.projectroot,
                           ".tx", 'config')

    with open(tx_conf, 'r') as f:
        files = [ l.rsplit(' ', 1)[1].strip()
                  for l in f.readlines()
                  if l.startswith('source_file')]

    errs = 0
    for fn in files:
        fqfn = os.path.join(conf.paths.projectroot, fn)

        if not os.path.exists(fqfn):
            errs += 1
            logger.error(fqfn + " does not exist.")

    if errs != 0:
        logger.warning("{0} files configured that don't exist.")
    else:
        logger.info('all configured translation source files exist')

    return errs

#################### Task Generators ####################

def pull_tasks(conf, app):
    resources = tx_resources(conf)

    for page in resources:
        t = app.add('task')
        t.job = logged_command
        t.args = ('pull', ' '.join([ 'tx', 'pull', '-l', lang, '-r', page]))
        t.description = 'pulling {0} from transifex client'.format(page)

def push_tasks(conf, app):
    resources = tx_resources(conf)

    for page in resources:
        t = app.add('task')
        t.job = logged_command
        t.args = ('pull', ' '.join([ 'tx', 'pull', '-l', lang, '-r', page]))
        t.description = 'pulling {0} from transifex client'.format(page)

def update(conf):
    logger.info('updating translation artifacts. Long running.')

    project_name = conf.project.title.lower().split()
    if conf.project.edition is not None and conf.project.edition != conf.project.name:
        project_name.append(conf.project.edition)

    project_name = '-'.join(project_name)

    logger.info('starting translation upload with sphinx-intl')

    flogger = FileLogger(logger)
    update_txconfig_resources(transifex_project_name=project_name,
                              locale_dir=conf.paths.locale,
                              pot_dir=os.path.join(conf.paths.locale, 'pot'),
                              out=flogger)

    logger.info('sphinx-intl: updated pot directory')

#################### Commands ####################

@argh.named('check')
@argh.expects_obj
def check_orphaned(args):
    conf = fetch_config(args)

    check_for_orphaned_tx_files(conf)

@argh.arg('--edition', '-e')
@argh.arg('--language', '-l')
@argh.named('update')
@argh.expects_obj
def update_translations(args):
    conf = fetch_config(args)

    update(conf)
    check_for_orphaned_tx_files(conf)

@argh.named('pull')
@argh.expects_obj
def pull_translations(args):
    conf = fetch_config(args)

    app = BuildApp.new(pool_type=conf.runstate.runner,
                       pool_size=conf.runstate.pool_size,
                       force=conf.runstate.force)

    pull_tasks(conf, app)
    app.run()

@argh.arg('--edition', '-e')
@argh.arg('--language', '-l')
@argh.named('push')
@argh.expects_obj
def push_translations(args):
    conf = fetch_config(args)

    app = BuildApp.new(pool_type=conf.runstate.runner,
                       pool_size=conf.runstate.pool_size,
                       force=conf.runstate.force)

    push_tasks(conf, app)

    update(conf)
    app.run()
