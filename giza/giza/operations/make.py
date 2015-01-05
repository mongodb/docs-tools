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

import logging

import argh

from giza.core.app import BuildApp
from giza.config.helper import fetch_config
from giza.config.project import EditionListConfig
from giza.operations.deploy import deploy_worker
from giza.operations.sphinx_cmds import sphinx_publication
from giza.operations.build_env import package_build_env, env_package_worker
from giza.tools.timing import Timer

logger = logging.getLogger('giza.operations.make')

def build_reporter(target, deploy_action, make_packages, build_sphinx, editions, languages, args):
    """
    Infers what the "traditional" direct ``giza`` command would be given
    information from the ``make`` target, to make the ``make`` emulation
    operation less opaque.
    """

    if len(deploy_action) > 0:
        deploy_action = ' '.join(deploy_action)

    target_set = set()
    for t in target:
        if isinstance(t, list):
            target_set.update(t)
        else:
            target_set.add(t)

    target = list(target_set)
    if make_packages is True:
        cmd = "giza env --builder "  + ' '.join(target)
    elif deploy_action:
        if build_sphinx:
            cmd = 'giza push --deploy ' + deploy_action + ' --builder ' + ' '.join(target)
        else:
            cmd = 'giza deploy --target ' + deploy_action
    else:
        cmd = 'giza sphinx --builder ' + ' '.join(target)

    if build_sphinx or make_packages:
        if editions and None not in editions:
            cmd += ' --edition ' + ' '.join(editions)
        if languages and None not in languages:
            cmd += ' --languages ' + ' '.join(languages)

    if args.serial_sphinx is True:
        cmd += ' --serial_sphinx'

    return cmd

def determine_workload(targets, conf):
    """
    Given a string of ``make``-like targets, returns a

    :returns: A boolean that is ``False`` when the operation is *just* and
        ``True`` when the operation requires a Sphinx invocation.

    :rtype: bool, list
    """
    build_sphinx = True
    make_packages = False
    deploy_actions = []

    if targets[0] in ('deploy', 'stage', 'push'):
        target = ['publish']

        if targets[0] == 'giza':
            targets = targets[1:]

        if targets[0] == 'deploy':
            build_sphinx = False
            targets = targets[1:]

        target_str = '-'.join(targets)

        for t in conf.system.files.data.push:
            if targets[0].startswith(t['target']) or target_str.startswith(t['target']):
                deploy_action.append( t['target'])
    elif targets[0] == 'env':
        build_sphinx = False
        make_packages = True
        target = targets[1:]
    elif targets[0].startswith('package'):
        logger.error("make interface does not contain support for artifact packaging")
    else:
        supported_targets = set([ target.split('-')[0]
                                  for target in conf.system.files.data.integration['base']['targets']
                                  if '/' not in target and
                                  not target.startswith('htaccess') ])

        target = []
        for t in targets:
            if t in supported_targets:
                target.append(t)

        if not target:
            target = ['publish']

    return build_sphinx, make_packages, target, deploy_actions

@argh.arg('make_target', nargs="*")
@argh.arg('--serial_sphinx', action='store_true')
@argh.named('make')
@argh.expects_obj
def main(args):
    """
    Emulates ``make``. Pass a list of make targets. Most projects call this
    using a simple Makefile pass through.

    Calls the underlying functions from ``giza deploy`` and ``giza sphinx``.
    """

    conf = fetch_config(args)
    targets = [ t.split('-') for t in args.make_target ]

    build_sphinx = True
    make_packages = False
    deploy_action = []
    sphinx_targets = []

    for t in targets:
        should_build, should_make_packages, sphinx_targets, deploys = determine_workload(t, conf)

        sphinx_targets.extend(sphinx_targets)
        deploy_action.extend(deploys)

        if make_packages is False and should_make_packages is True:
            make_packages = should_make_packages
        if build_sphinx is True and should_build is False:
            build_sphinx = should_build

    sphinx_targets = list(set(sphinx_targets))

    editions = []
    languages = []
    for target_options in targets:
        for option in target_options:
            if option in conf.project.edition_list:
                editions.append(option)

        target_string = '-'.join(target_options)
        if target_string in conf.system.files.data.integration:
            languages.append(target_string)

    if not editions:
        if len(conf.project.editions) > 0:
            editions = conf.project.edition_list
        else:
            editions = [None]

    if not languages:
        languages = [None]

    cmd = build_reporter(sphinx_targets, deploy_action, make_packages, build_sphinx, editions, languages, args)
    logger.info('running: ' + cmd)

    args.push_targets = deploy_action
    args.languages_to_build = languages
    args.editions_to_build = editions
    args.builder = sphinx_targets
    conf.runstate = args

    app = BuildApp(conf)

    if build_sphinx:
        with Timer("full sphinx build for: " + ' '.join(sphinx_targets)):
            sphinx_publication(conf, args, app)

    if deploy_action:
        with Timer("deploy build for: " + ' '.join(sphinx_targets)):
            deploy_worker(conf, app)

    if make_packages:
        with Timer("making packages for: " + ' '.join(sphinx_targets)):
            env_package_worker(conf.runstate, conf)
