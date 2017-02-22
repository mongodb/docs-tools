#  2014 MongoDB, Inc.
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
Contains the output specification for redirects (i.e. ``.htaccess`` files,) as
well as integration into the :class:`giza.libgiza.app.BuildApp()`
infrastructure. All of the data processing and definition happens in
:mod:`giza.config.redirects`.
"""

import os.path
import logging

import giza.libgiza.task

logger = logging.getLogger('giza.content.post.redirects')


def make_redirect(conf):
    o = []

    logger.info('generating {0} redirects'.format(len(conf.system.files.data.htaccess)))
    for redir in conf.system.files.data.htaccess:
        if redir.to.startswith('http'):
            url = redir.to
        else:
            url = conf.project.url + redir.to

        if url.endswith('/'):
            url = url[:-1]

        o.append(' '.join(['Redirect', str(redir.code), redir.from_loc, url, '\n']))

    o.sort()
    o.extend(['\n',
              '<FilesMatch "\.(ttf|otf|eot|woff)$">', '\n',
              '   Header set Access-Control-Allow-Origin "*"', '\n',
              '</FilesMatch>',
              ])

    return o


def write_redirects(fn, conf):
    if not os.path.exists(os.path.dirname(fn)):
        os.makedirs(os.path.dirname(fn))

    with open(fn, 'w') as f:
        f.writelines(make_redirect(conf))
        f.write('\n')

    logger.info('wrote redirects to: ' + fn)


def redirect_tasks(conf):
    tasks = []

    if conf.git.branches.current != 'master':
        return tasks

    if 'htaccess' in conf.system.files.data:
        fn = os.path.join(conf.paths.projectroot, conf.paths.htaccess)

        deps = []
        for configfn in conf.system.files.paths:
            if isinstance(configfn, dict):
                if 'htaccess' in configfn:
                    deps.extend([os.path.join(conf.paths.projectroot, conf.paths.builddata, rfn)
                                 for rfn in configfn['htaccess']])
            elif configfn.startswith('htaccess'):
                deps.append(os.path.join(conf.paths.projectroot, conf.paths.builddata, configfn))

        tasks.append(giza.libgiza.task.Task(job=write_redirects,
                                            args=(fn, conf),
                                            target=fn,
                                            dependency=deps,
                                            description=' '.join(('generate and write redirects into:',
                                                                  conf.paths.htaccess))))

    logger.info("added {0} redirect generation tasks".format(len(tasks)))
    return tasks
