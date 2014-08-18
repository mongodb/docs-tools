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

import datetime
import itertools
import json
import logging
import os

import argh
import yaml

logger = logging.getLogger('giza.scrumpy')

from giza.config.jeerah import fetch_config, JeerahRuntimeStateConfig
from giza.config.helper import dump_skel
from giza.config.credentials import setup_credentials
from giza.cmdline import get_base_parser
from giza.core.app import BuildApp
from giza.jeerah.client import JeerahClient
from giza.jeerah.query import strip_name

import giza.jeerah.progress
import giza.jeerah.triage

#################### helpers #####################

def pprint(obj):
    print(json.dumps(obj, indent=3))

#################### scrumpy commands #####################

def config(args):
    conf = fetch_config(args)

    dynamics = [ conf.site, conf.runstate, conf.buckets, conf.sprints,
                 conf.reporting, conf.modification ]

    pprint(json.dumps(conf.dict(), indent=3))

@argh.arg('--sprint')
def progress(args):
    conf = fetch_config(args)
    app = BuildApp(conf)
    app.pool = 'thread'

    j = JeerahClient(conf)
    j.connect()

    query_data = giza.jeerah.progress.query(j, app, conf)

    pprint(giza.jeerah.progress.report(query_data, conf))

def triage(args):
    conf = fetch_config(args)
    app = BuildApp(conf)
    app.pool = 'thread'

    j = JeerahClient(conf)
    j.connect()

    query_data = giza.jeerah.triage.query(j, app, conf)

    pprint(giza.jeerah.triage.report(query_data, conf))

#################### Jira Modification Tasks ####################

@argh.named('create-versions')
@argh.arg('--sprint')
@argh.arg('--project')
def make_versions(args):
    conf = fetch_config(args)

    j = JeerahClient(conf)
    j.connect()

    current_versions = [strip_name(v.name) for v in j.versions(conf.runstate.project)]

    created = []
    for v in getattr(conf.sprints, conf.runstate.sprint):
        v = strip_name(v)
        if v not in current_versions:
            j.create_version(conf.runstate.project, v, release=False)
            created.append(v)
            logger.info('creating new version {0} in project {1}'.format(v, conf.runstate.project))
        else:
            logger.info('version {0} already exists in project {1}'.format(v, conf.runstate.project))

    pprint({ 'created': created, 'project': conf.runstate.project })

@argh.named('mirror-versions')
def mirror_version(args):
    results = { 'created': {}, 'targets': {} }

    conf = fetch_config(args)

    j = JeerahClient(conf)
    j.connect()

    source_project = conf.modification.mirroring.source

    results['sources'] = [ strip_name(v.name)
                           for v in j.versions(source_project)
                         ]

    for target_project in conf.modification.mirroring.target:
        results['created'][target_project] = []
        results['targets'][target_project] = [ v.name
                                               for v in j.versions(target_project)
                                              ]
        for i in results['sources']:
            if i not in results['targets'][target_project]:
                j.create_version(target_project, i, '', False)
                logger.info('created version named "{0}" in {1} project'.format(i, target_project))
                results['created'][target_project].append(i)
            else:
                logger.info('project {0} exists. passing.'.format(i))

    pprint(results)

def release(args):
    results = { }

    conf = fetch_config(args)

    j = JeerahClient(conf)
    j.connect()

    for project in conf.site.projects:
        results[project] = []
        current = j.versions(project)

        for version in conf.sprints.current:
            for v in current:
                if v.name in version:
                    logger.debug('archiving {0} in project {1}'.format(v.name, project))
                    j.archive_version(v)
                    j.release_version(v)
                    results[project].append(v.name)
                else:
                    logger.debug('{0} is not eligible for release'.format(v.name))

    pprint({ 'released': results, 'code': 200 })


@argh.arg('--path', dest='user_conf_path', default='.scrumpy.yaml')
def setup(args):
    skel = {
        'site': { 'credentials': "~/.giza-credentials.yaml",
                  'projects': ['DOCS', 'TOOLS', 'INTERNAL'],
                  'url': "https://jira.example.net/" },
        'sprints': { 'previous': [ 'sprint-0', 'release-0' ],
                     'current': [ 'spirnt-1', 'release-1'],
                     'next': [ 'spirnt-2', 'release-2'],
                     'future': [ 'spirnt-3', 'release-3'],
                     'archived': [
                         [ 'legacy-0', 'legacy-release-0'],
                         [ 'legacy-1', 'legacy-release-1']
                      ],
        },
        'buckets': {
            'next': 'docs-next',
            'planning': 'docs-planning',
            'triage': 'docs-triage'
        },
        'reporting': {
            'units': 'days',
            'format': 'json'
        },
        'modification': {
            'mirroring': {
                'source': 'DOCS',
                'target': 'INTERNAL'
            }
        }
    }

    dump_skel(skel, args)

@argh.named('setup-credentials')
def setup_credential_file(args):
    setup_credentials(args)

#################### scrumpy entry point #####################

def main():
    parser = get_base_parser()

    commands = [setup, setup_credential_file, config, progress, triage,
                make_versions, mirror_version, release]

    argh.add_commands(parser, commands)

    args = JeerahRuntimeStateConfig()

    if args.level == 'info':
        args.level = 'warning'

    argh.dispatch(parser, namespace=args)
