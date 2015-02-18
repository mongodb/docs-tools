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
import json

import argh

from github3 import login

from giza.config.helper import dump_skel
from giza.config.github import fetch_config, GithubRuntimeConfig
from giza.config.credentials import CredentialsConfig
from giza.cmdline import get_base_parser
from giza.corp import get_contributor_list
from libgiza.app import BuildApp

logger = logging.getLogger('giza.github')

try:
    # Python 2
    prompt = raw_input
except NameError:
    # Python 3
    prompt = input

# mdbpr helpers


def collect_two_factor_token():
    code = ''
    while not code:
        # The user could accidentally press Enter before being ready,
        # let's protect them from doing that.
        code = prompt('Enter 2FA code: ')
    return code


def get_connection(conf):
    credentials = CredentialsConfig(conf.site.credentials).github

    if 'token' in credentials:
        gh = login(token=credentials.token)
    else:
        gh = login(credentials.username, credentials.password,
                   two_factor_callback=collect_two_factor_token)

    return gh


def pprint(doc):
    print(json.dumps(doc, indent=3))

# mdbpr data handling workers


def get_pull_requests(gh, repo, approved_users):
    r = gh.repository(repo.user, repo.name)
    results = []

    if r is None:
        return results

    for pull in r.iter_pulls():
        results.append({
            'url': str(pull.html_url),
            'user': str(pull.user.login),
            'merge_safe': True if pull.user.login in approved_users else False,
        })

    return results


def get_github_org_members(gh, org):
    return [user.login
            for user in gh.organization(org).iter_members()]


def mine_github_pulls(gh, app, conf):
    results = []

    try:
        approved_users = get_contributor_list(conf)
    except:
        approved_users = []

    corpt = app.add('task')
    corpt.job = get_contributor_list
    corpt.args = [conf]

    for org in conf.organizations:
        t = app.add('task')
        t.job = get_github_org_members
        t.args = [gh, org]
        t.description = 'get users from github org "{0}"'.format(org)

    app.run()

    for r in app.results:
        approved_users.extend(r)

    app.reset()

    for repo in conf.repos:
        t = app.add('task')
        t.job = get_pull_requests
        t.args = [gh, repo, approved_users]
        t.description = 'mine pull requests from {0}'.format(repo.name)

    app.run()

    for r in app.results:
        results.extend(r)

    return results

# mdbpr commands


@argh.arg('--path', dest='conf_path', default='.github.yaml')
@argh.expects_obj
def setup(args):
    skel = {
        'site': {'credentials': "~/.giza-credentials.yaml",
                 'corp': None},
        'repos': [{'user': 'mongodb', 'name': 'docs'},
                  {'user': 'mongodb', 'name': 'docs-ecosystem'}],
        'organizations': ['mongodb', '10gen'],
        'reporting': {'format': 'json'},
    }

    dump_skel(skel, args)


@argh.expects_obj
def mine(args):
    conf = fetch_config(args)
    app = BuildApp(conf)
    app.pool_size = 4

    gh = get_connection(conf)

    pprint(mine_github_pulls(gh, app, conf))


@argh.expects_obj
def stats(args):
    conf = fetch_config(args)
    app = BuildApp(conf)
    app.pool_size = 4
    gh = get_connection(conf)

    users = set()
    result = {'merge_safe': 0, 'total': 0}
    for pull in mine_github_pulls(gh, app, conf):
        result['total'] += 1
        if pull['merge_safe'] is True:
            result['merge_safe'] += 1

        users.add(pull['user'])

    result['user_count'] = len(users)
    result['users'] = list(users)

    pprint(result)


@argh.expects_obj
def actions(args):
    conf = fetch_config(args)
    app = BuildApp(conf)
    app.pool_size = 4
    gh = get_connection(conf)

    results = []

    for pull in mine_github_pulls(gh, app, conf):
        if pull['merge_safe'] is True:
            results.append(pull)

    pprint(results)

# mdbpr entry point


def main():
    parser = get_base_parser()

    commands = [mine, stats, actions, setup]

    argh.add_commands(parser, commands)

    args = GithubRuntimeConfig()

    if args.level == 'info':
        args.level = 'warning'

    if args.runner == 'process':
        logger.warning('this operation does not support multiprocessing, falling back to threads')
        args.runner = 'thread'
    argh.dispatch(parser, namespace=args)
