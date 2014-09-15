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
from giza.operations.deploy import deploy_worker
from giza.operations.sphinx import sphinx_publication

logger = logging.getLogger('giza.operations.make')

def build_reporter(target, deploy_action, build_sphinx, editions, languages):
    if not deploy_action: 
        cmd = 'giza sphinx --builder ' + ' '.join(target)
    else: 
        if build_sphinx:
            cmd = 'giza push --deploy ' + deploy_action[0] + ' --builder ' + ' '.join(target)
        else:
            cmd = 'giza deploy --target ' + deploy_action[0]

    if build_sphinx:
        if editions: 
            cmd += ' --edition ' + ' '.join(editions)
        if languages: 
            cmd += ' --languages ' + ' '.join(languages)

    return cmd

def determine_workload(targets, conf):
    build_sphinx = True
    deploy_action = []

    if targets[0] in ('deploy', 'stage', 'push'):
        offset = 0

        target = ['publish']

        if targets[0] == 'giza':
            targets = targets[1:]
            offset += 4

        if targets[0] == 'deploy':
            build_sphinx = False
            targets.pop('deploy')
            offset += 6
    
        for t in conf.system.files.data.push:
            if target[offset:].startswith(t['target']):
                deploy_action = [ t['target'] ]
                offset += len(t['target'])
                break
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

    return target, deploy_action, build_sphinx

@argh.arg('make_target')
@argh.named('make')
def main(args):
    conf = fetch_config(args)
    targets = args.make_target.split('-')

    target, deploy_action, build_sphinx = determine_workload(targets, conf)

    editions = []
    languages = []
    for rtarget in targets: 
        if rtarget in conf.project.edition_list:
            editions.append(rtarget)
        elif rtarget in conf.system.files.data.integration:
            languages.append(rtarget)

    cmd = build_reporter(target, deploy_action, build_sphinx, editions, languages)
    logger.info('running: ' + cmd)

    if not editions:
        editions = [None]
    if not languages:
        languages = [None]

    args.push_targets = deploy_action
    args.languages_to_build = languages
    args.editions_to_build = editions
    args.builder = target
    conf.runstate = args

    app = BuildApp(conf)

    if build_sphinx:
        sphinx_publication(conf, args, app)

    if deploy_action: 
        deploy_worker(conf, app)
