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
Giza can check and update inventories once per build-run rather than once per
build run. Useful for minimizing the start-up time for ``sphinx-build`` and
useful for reducing redundant work in parallel build situations.
"""

import time
import os
import logging
import subprocess

import libgiza.task

from giza.tools.files import verbose_remove, safe_create_directory

logger = logging.getLogger('giza.content.intersphinx')

ACCEPTABLE = 864000

# Helper functions


def download_file(file, url):
    cmd = ['curl', '-s', '--remote-time', url, '-o', file]

    safe_create_directory(os.path.dirname(file))

    try:
        subprocess.check_call(cmd)
        logger.info('downloaded {0}'.format(file))
        return True
    except subprocess.CalledProcessError:
        logger.error('trouble downloading interspinx inventory: ' + file)
        return False


def file_timestamp(path):
    return os.stat(path)[8]

# Tasks


def download(f, s, conf):
    if conf.runstate.force is True:
        newf = download_file(f, s)

    if os.path.isfile(f):
        newf = False
    else:
        logger.info('{0} file does not exist, downloading now'.format(f))
        newf = download_file(f, s)

        if newf is False:
            m = "intersphinx inventory ({0}) download failed. skipping"
            logger.warning(m.format(f))
            return

    mtime = file_timestamp(f)

    if mtime < time.time() - ACCEPTABLE:
        # if mtime is less than now - n days, it may be stale.

        newtime = time.time() - (ACCEPTABLE / 2)

        if newf is True:
            # if we just downloaded the file it isn't stale yet
            os.utime(f, (newtime, newtime))
        else:
            # definitley stale, must download it again.
            newf = download_file(f, s)
            if mtime == file_timestamp(f):
                # if the source is stale, modify mtime so we don't
                # download it for a few days.
                os.utime(f, (newtime, newtime))


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
        tasks.append(libgiza.task.Task(job=download,
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
            t = libgiza.task.Task(job=verbose_remove,
                                  args=[fn])
            tasks.append(t)

    return tasks
