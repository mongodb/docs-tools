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

import os
import json
import logging
import collections

import argh

from giza.core.git import GitRepo
from giza.config.code_review import CodeReviewConfiguration
from giza.config.helper import fetch_config, new_skeleton_config, new_credentials_config

from giza.operations.includes import render_for_console
from giza.tools.command import command

logger = logging.getLogger('giza.operations.code_review')

def safe_create_code_review_data_file(fn):
    if os.path.isfile(fn):
        return

    with open(fn, 'w') as f:
        json.dump({'branches': {}}, f)
        logger.info('created new code review cache')


def get_cr_data_file(arg):
    if isinstance(arg, GitRepo):
        path = arg.top_level()
    else:
        path = arg.paths.projectroot

    return os.path.join(path, '.git', 'code_review_mapping.json')

@argh.expects_obj
@argh.named('list')
def list_reviews(args):
    "Lists tracked code reviews."

    conf = fetch_config(args)
    cr_data_file = get_cr_data_file(conf)
    safe_create_code_review_data_file(cr_data_file)

    crconf = CodeReviewConfiguration(cr_data_file)

    render_for_console([ k for k in crconf.branches.keys()])

@argh.expects_obj
@argh.arg('_branch_name', nargs='*')
def close(args):
    "Removes a tracked code review."

    conf = new_skeleton_config(args)
    g = GitRepo()
    cr_data_file = get_cr_data_file(g)

    safe_create_code_review_data_file(cr_data_file)

    with CodeReviewConfiguration.persisting(cr_data_file) as data:
        branches = data.branches.keys()

        for to_delete in args._branch_name:
            if to_delete in branches:
                del data.branches[to_delete]
                logger.info('removed tracked code review for: ' + to_delete)
            else:
                logger.info("not tracking a code review for: " + to_delete)

            try:
                g.remove_branch(to_delete, args.force)
                logger.info('removed branch: ' + to_delete)
            except:
                logger.error('could not remove branch: ' + to_delete)

@argh.expects_obj
@argh.arg('_branch_name')
def checkout(args):
    "Checks out a tracked code review branch."

    conf = new_skeleton_config(args)
    g = GitRepo()
    cr_data_file = get_cr_data_file(g)

    safe_create_code_review_data_file(cr_data_file)
    crconf = CodeReviewConfiguration(cr_data_file)

    if args._branch_name in crconf.branches:
        try:
            g.checkout(args._branch_name)
            logger.info('checked out: ' + args._branch_name)
        except:
            logger.error('could not checkout branch: ' + args._branch_name)
    else:
        m = "no branch named {0} tracked. Please use another method to checkout this branch"
        logger.warning(m.format(args._branch_name))

@argh.named('send')
@argh.expects_obj
def create_or_update(args):
    "Creates or updates a code review case."

    creds = new_credentials_config()
    conf = new_skeleton_config(args)
    g = GitRepo()
    cr_data_file = get_cr_data_file(g)

    safe_create_code_review_data_file(cr_data_file)

    with CodeReviewConfiguration.persisting(cr_data_file) as data:
        if g.current_branch() in data.branches:
            cr_data = data.branches[g.current_branch()]
            if len(cr_data.commits) > 1 and g.sha('HEAD~') == cr_data.commits[-2]:
                # the last commit was amended, so replace it:
                if g.sha('HEAD') != cr_data.commits[-1]:
                    cr_data.commits[-1] = g.sha('HEAD')
            elif g.sha() not in cr_data.commits:
                cr_data.commits.append(g.sha())

            if len(cr_data.commits) >= 2:
                use_hash = str('..'.join([cr_data.commits[0][0:8], cr_data.commits[-1][0:8]]))
            else:
                use_hash = str(cr_data.commits[-1])

            logger.info('updating an existing code review.')
            update_code_review(cr_data, g, use_hash)
        else:
            data.set_branch(g.current_branch(), { 'original_name': g.commit_messages()[0],
                                                  'commits': [ g.sha('HEAD~'), g.sha() ],
                                    })

            logger.info('creating new code review.')
            create_code_review(data, g, creds)

##### Worker functions to create or update code reviews

def update_code_review(cr_data, g, use_hash):
    cmd = [
        'upload.py',
        '-y',
        '--nojira',
        '--email', g.author_email(),
        '-m', '"'+ cr_data.original_name + '"',
        '-i', cr_data.issue
    ]

    if len(cr_data.commits) > 2:
        cmd.append('--rev')

    cmd.append(use_hash)
    cr_upload = command(cmd, capture=True)

    issue_url = get_issue_url(cr_upload.out)
    if issue_url is not None:
        logger.info('updated issue: ' + issue_url)
    else:
        logger.error('failed to update issue')

def create_code_review(data, g, creds):
    branch_data = data.get_branch(g.current_branch())

    cmd = ['upload.py', '-y']

    if creds is not None:
        cmd.extend(['--jira_user', creds.jira.username])

    cmd.extend([ '--email', g.author_email(),
                 '-m', '"' + g.commit_messages()[0] + '"',
                 branch_data.commits[-1]])

    cr_upload = command(cmd, capture=True)
    branch_data.issue = get_issue_number(cr_upload.out)
    data.set_branch(g.current_branch(), branch_data)

    issue_url = get_issue_url(cr_upload.out)
    if issue_url is None:
        logger.error('failed to create issue')
    elif len(issue_url) < 80:
        logger.info('created issue: ' + issue_url)
    else:
        logger.info('created new code review issue')

##### Output processing

def get_issue_url(output):
    if not isinstance(output,list):
        output = output.split('\n')

    for ln in output:
        if 'http' in ln:
            return ln.split(' ')[-1]

def get_issue_number(output):
    if not isinstance(output,list):
        output = output.split('\n')

    for ln in output:
        if ln.startswith("Issue "):
            return ln.rsplit('/', 1)[-1]

    # if we get here, we're in trouble:
    logger.error('did not create an issue')
    print('\n'.join(output))
    raise Exception
