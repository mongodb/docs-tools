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
Alternate implementation of the system that fetches intersphinx inventories from
other Sphinx sites. Implemented separately to avoid using Sphinx so that that
Giza can check and update inventories once per day rather than once per
build run. Useful for minimizing the start-up time for ``sphinx-build`` and
useful for reducing redundant work in parallel build situations.
"""

import email.utils
import logging
import os
import time
from six.moves import urllib

import giza.libgiza.task

from giza.tools.files import verbose_remove, safe_create_directory

logger = logging.getLogger('giza.content.intersphinx')

MAX_AGE = 60 * 60 * 24 * 1  # One day
TIMEOUT_SECONDS = 5


def download(path, url, conf):
    try:
        mtime = os.stat(path).st_mtime
    except OSError:
        mtime = -1

    now = time.time()
    if now < (mtime + MAX_AGE):
        logger.debug('Intersphinx file still young: %s', url)
        return

    request = urllib.request.Request(url, headers={
        'If-Modified-Since': email.utils.formatdate(mtime)
    })

    safe_create_directory(os.path.dirname(path))

    try:
        response = urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS)
        with open(path, 'wb') as f:
            f.write(response.read())
    except urllib.error.HTTPError as err:
        if err.code == 304:
            logger.debug('Not modified: %s', url)
            return
        logger.error('Error downloading %s: Got %d', url, err.code)
    except urllib.error.URLError as err:
        logger.error('Error downloading %s: %s', url, str(err))


def intersphinx_tasks(conf):
    if 'intersphinx' not in conf.system.files.data:
        return

    tasks = []
    for i in conf.system.files.data.intersphinx:
        try:
            f = os.path.join(conf.paths.projectroot,
                             conf.paths.output, i.path)

            s = i.url + 'objects.inv'
        except AttributeError:
            f = os.path.join(conf.paths.projectroot,
                             conf.paths.output, i['path'])

            s = i['url'] + 'objects.inv'

        description = 'download intersphinx inventory from {0}'.format(s)
        tasks.append(giza.libgiza.task.Task(job=download,
                                            args=(f, s, conf),
                                            target=f,
                                            dependency=None,
                                            description=description))
        logger.debug('added job for {0}'.format(s))

    return tasks


def intersphinx_clean(conf):
    tasks = []

    for inv in conf.system.files.data.intersphinx:
        try:
            fn = os.path.join(conf.paths.projectroot,
                              conf.paths.output, inv.path)
        except AttributeError:
            fn = os.path.join(conf.paths.projectroot,
                              conf.paths.output, inv['path'])

        if os.path.exists(fn):
            t = giza.libgiza.task.Task(job=verbose_remove,
                                       args=[fn])
            tasks.append(t)

    return tasks
