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
import os.path

logger = logging.getLogger('giza.content.assets')

from giza.core.git import GitRepo
from giza.tools.files import rm_rf
from giza.tools.command import command

def assets_setup(path, branch, repo):
    if os.path.exists(path):
        g = GitRepo(path)
        g.pull(branch=branch)
        logger.info('updated {0} repository'.format(path))
    else:
        base, name = os.path.split(path)

        g = GitRepo(base)

        g.clone(repo, repo_path=name, branch=branch)
        logger.info('cloned {0} branch from repo {1}'.format(branch, repo))


def assets_tasks(conf, app):
    if conf.assets is not None:
        gen_app = app.add('app')

        for asset in conf.assets:
            path = os.path.join(conf.paths.projectroot, asset.path)

            logger.debug('adding asset resolution job for {0}'.format(path))

            t = app.add('task')
            t.job = assets_setup
            t.args = { 'path': path,
                       'branch': asset.branch,
                       'repo': asset.repository }

            if 'generate' in asset:
                for content_type in asset.generate:
                    t = gen_app.add('task')
                    t.job = command
                    t.args = 'cd {0}; giza generate {1}'.format(path, content_type)

def assets_clean(conf, app):
    if conf.assets is not None:
        for asset in conf.assets:
            path = os.path.join(conf.paths.projectroot, asset.path)

            logger.debug('adding asset cleanup {0}'.format(path))

            t = app.add('task')
            t.job = rm_rf
            t.args = [path]
