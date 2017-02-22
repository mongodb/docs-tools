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
:mod:`~giza.content.assets` makes it possible to configure embedded `git`
repositories within a ``giza`` configured project. These repositories may either
be updated to the latest revision upon every build or are pinned to a specific
revision in the configuration file.

Assets specifications are in the top level of the build configuration accessible
via the ``assets`` field in a :class:`~giza.config.main.Configuration` instance,
which holds a list of repository definitions, which resembles the following: ::

   {
     "branch": <string>,
     "path": <path>,
     "repository": <url>
   }


.. describe:: assets.branch

   The name of a remote branch in the repository.

.. describe:: assets.path

   A local path for the cloned repository. Relative to the top of the repository.

.. describe:: assets.repository

   A git-compatible URL for the source repository.

A future version of the assets system may allow users to specify a specific
revision rather than a branch so that builds for specific branches are more
stable over time.
"""

import logging
import os
import shutil
import subprocess

import giza.libgiza.task
import giza.libgiza.git

import giza.tools.files

logger = logging.getLogger('giza.content.assets')


def assets_setup(path, branch, repo, commit=None):
    """
    Worker function that clones a repository if one doesn't exist and pulls
    the repository otherwise.
    """
    # TODO: In the future this should be able to pin the repository to a
    #       specific hash.

    if os.path.exists(path):
        g = giza.libgiza.git.GitRepo(path)

        if commit is None:
            try:
                g.pull(branch=branch)
            except giza.libgiza.git.GitError as error:
                logger.error('failed to pull %s repository', path)
                logger.debug(error)
                return

            logger.info('updated %s repository', path)
            return
        elif g.sha() == commit or g.sha().startswith(commit):
            logger.info('repository %s is currently at (%s)', path, commit)
        else:
            g.checkout(commit)
            logger.info('update %s repository to (%s)', path, commit)
    else:
        base, name = os.path.split(path)
        giza.tools.files.safe_create_directory(base)

        g = giza.libgiza.git.GitRepo(base)
        g.clone(repo, repo_path=path, branch=branch)
        logger.info('cloned %s branch from repo %s', branch, repo)

        if commit is not None and (g.sha() == commit or g.sha().startswith(commit)):
            g.checkout(commit)
            logger.info('repository %s is currently at (%s)', path, commit)


def assets_tasks(conf):
    """Add tasks to an app to create/update the assets."""

    tasks = []
    generate_tasks = []
    if conf.assets is not None:
        giza.tools.files.safe_create_directory(conf.paths.projectroot)
        for asset in conf.assets:
            path = os.path.join(conf.paths.projectroot, asset.path)

            logger.debug('adding asset resolution job for %s', path)

            args = {'path': path,
                    'branch': asset.branch,
                    'repo': asset.repository}

            if 'commit' in asset:
                args['commit'] = asset.commit

            description = "setup assets for: {0} in {1}".format(asset.repository, path)
            tasks.append(giza.libgiza.task.Task(job=assets_setup,
                                                args=args,
                                                target=path,
                                                dependency=None,
                                                description=description))

            # If you specify a list of "generate" items, giza will call ``giza
            # generate`` to build content after updating the
            # repository. Deprecated, and largely unused.
            if 'generate' in asset:
                for content_type in asset.generate:
                    description = 'generating objects in {0}'.format(path)
                    args = dict(cwd=path, args=['giza', 'generate', content_type])
                    generate_tasks.append(giza.libgiza.task.Task(job=subprocess.call,
                                                                 target=path,
                                                                 dependency=None,
                                                                 args=args,
                                                                 description=description))

    if len(generate_tasks) > 0:
        tasks.append(generate_tasks)

    return tasks


def assets_clean(conf):
    """Adds tasks to remove all asset repositories."""

    tasks = []

    if conf.assets is not None:
        for asset in conf.assets:
            path = os.path.join(conf.paths.projectroot, asset.path)
            logger.debug('adding asset cleanup %s', path)

            t = giza.libgiza.task.Task(job=shutil.rmtree,
                                       args=[path],
                                       target=path,
                                       dependency=None,
                                       description='cleaning up asset: ' + path)

            tasks.append(t)

    return tasks
