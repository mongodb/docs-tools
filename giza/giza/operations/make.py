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
from giza.tools.timing import Timer

logger = logging.getLogger('giza.operations.make')

def build_reporter(target, deploy_action, build_sphinx, editions, languages, args):
    if len(deploy_action) > 0:
        deploy_action = ' '.join(deploy_action)

    target_set = set()
    for t in target:
        if isinstance(t, list):
            target_set.update(t)
        else:
            target_set.add(t)

    target = list(target_set)
    if not deploy_action:
        cmd = 'giza sphinx --builder ' + ' '.join(target)
    else:
        if build_sphinx:
            cmd = 'giza push --deploy ' + deploy_action + ' --builder ' + ' '.join(target)
        else:
            cmd = 'giza deploy --target ' + deploy_action

    if build_sphinx:
        if editions and None not in editions:
            cmd += ' --edition ' + ' '.join(editions)
        if languages and None not in languages:
            cmd += ' --languages ' + ' '.join(languages)

    if args.serial_sphinx is True:
        cmd += ' --serial_sphinx'

    return cmd

def determine_workload(deploy_action, targets, conf):
    build_sphinx = True
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

    return build_sphinx, target

@argh.arg('make_target', nargs="*")
@argh.arg('--serial_sphinx', action='store_true')
@argh.named('make')
@argh.expects_obj
def main(args):
    conf = fetch_config(args)
    targets = [ t.split('-') for t in args.make_target ]

    build_sphinx = True
    deploy_action = []

    sphinx_targets = set()
    for t in targets:
        should_build, sp = determine_workload(deploy_action, t, conf)
        sphinx_targets.update(sp)
        if build_sphinx is True and should_build is False:
            build_sphinx = should_build

    sphinx_targets = list(sphinx_targets)

    editions = []
    languages = []
    for rt in targets:
        for t in rt:
            if t in conf.project.edition_list:
                editions.append(t)

        rtarget = '-'.join(rt)
        if rtarget in conf.system.files.data.integration:
            languages.append(rtarget)

    if not editions:
        if len(conf.project.editions) > 0:
            editions = conf.project.edition_list
        else:
            editions = [None]
    if not languages:
        languages = [None]

    cmd = build_reporter(sphinx_targets, deploy_action, build_sphinx, editions, languages, args)
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
