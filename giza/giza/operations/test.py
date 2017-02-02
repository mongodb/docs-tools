# Copyright 2015 MongoDB, Inc.
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

import argh
import os
import logging
import subprocess
import shlex
import shutil

import giza.libgiza.git
import giza.libgiza.app
import giza.libgiza.task

import giza.content.assets
import giza.config.helper
import giza.config.main
import giza.tools.files

logger = logging.getLogger('GIZA.OPERATIONS.TEST')


def setup_test_repo(path, project):
    if os.path.isdir(path):
        g = giza.libgiza.git.GitRepo(path)
        if g.current_branch() != 'master':
            g.checkout_branch('master')
        g.pull(remote='origin', branch='master')
        logger.info('updated repository at: ' + path)
    else:
        g = giza.libgiza.git.GitRepo(os.path.dirname(path))
        g.clone(project.uri, os.path.basename(path))
        logger.info('cloned new repository into: ' + path)

    return project


def get_test_config(args):
    try:
        conf = giza.config.helper.fetch_config(args)
    except RuntimeError:
        path = os.path.join('data', 'build_config.yaml')
        if not os.path.isfile(path):
            logger.warning('must run test from the docs-tools repo, or a giza project directory.')
            raise SystemExit(-1)
        else:
            args.conf_path = path

            conf = giza.config.main.Configuration()
            conf.ingest(args.conf_path)
            conf.runstate = args
            conf.paths.projectroot = os.getcwd()

    return conf


def change_branch(path, branch):
    g = giza.libgiza.git.GitRepo(path)
    tracking = '/'.join(('origin', branch))

    if g.branch_exists(branch) is True:
        g.checkout(branch)
        g.pull(remote='origin', branch=branch)
        logger.info('checked out and updated {0} ({1}) in {2}'.format(branch, tracking, g.path))
    else:
        g.checkout_branch(branch, tracking=tracking)

        logger.info('checked out {0} ({1}) in {2}'.format(branch, tracking, g.path))


def run_test_op(cmd, dir):
    g = giza.libgiza.git.GitRepo(dir)

    r = subprocess.call(args=shlex.split(cmd), cwd=dir)
    if r != 0:
        m = 'failure with {0}, in "{1}", ({2})'.format(cmd, dir, g.current_branch())
        logger.error(m)
        raise RuntimeError(m)
    else:
        logger.info('completed {0}, in "{1}", ({2})'.format(cmd, dir, g.current_branch()))
        return 0


def cleaner(path):
    rm_path = os.path.join(path, "build")
    if not os.path.exists(rm_path):
        logger.info('directory is clean: ' + rm_path)
    else:
        shutil.rmtree(os.path.join(path, "build"))
        logger.info("removed path: " + rm_path)


integration_targets = ('complete', 'minimal', 'cleanComplete', 'cleanMinimal')


@argh.arg('--branch', '-b', dest='_override_branch', nargs="*", default=None)
@argh.arg('--project', '-p', dest='_override_projects', nargs="*", default=None)
@argh.arg('--operation', '-o', dest='_test_op', default='complete', choices=integration_targets)
@argh.expects_obj
@argh.named('test')
def integration_main(args):
    conf = get_test_config(args)
    app = giza.libgiza.app.BuildApp.new(pool_type=conf.runstate.runner,
                                        pool_size=conf.runstate.pool_size,
                                        force=conf.runstate.force)

    build_path = os.path.join(conf.paths.projectroot, conf.paths.output)

    giza.tools.files.safe_create_directory(build_path)

    for project in conf.test.projects:
        if (args._test_op not in project.operations and
                args._test_op.lower()[5:] not in project.operations):
            m = 'operation {0} not defined for project {1}'
            logger.error(m.format(args._test_op, project))
            continue

        if (args._override_projects is not None and
                project.project not in args._override_projects):
            continue

        if args._override_branch is not None:
            project.branches = args._override_branch

        if project.root is None:
            path = os.path.join(build_path, project.project)
            git_path = path
        else:
            path = os.path.join(build_path, project.project, project.root)
            git_path = os.path.join(build_path, project.project)

        task = app.add(giza.libgiza.task.Task(job=setup_test_repo,
                                              args=(git_path, project),
                                              ignore=False))

        if args._test_op.startswith('clean'):
            task = task.add_finalizer(giza.libgiza.task.Task(job=cleaner,
                                                             args=[path],
                                                             ignore=False))

        for branch in project.branches:
            task = task.add_finalizer(giza.libgiza.task.Task(job=change_branch,
                                                             args=(path, branch),
                                                             ignore=False))

            if args._test_op.startswith('clean'):
                op_name = args._test_op.lower()[5:]
            else:
                op_name = args._test_op

            for op in project.operations[op_name]:
                task = task.add_finalizer(giza.libgiza.task.Task(job=run_test_op,
                                                                 args=(op, path),
                                                                 ignore=False))

    app.run()
