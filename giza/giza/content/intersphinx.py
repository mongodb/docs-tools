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

import time
import os
import logging

logger = logging.getLogger('giza.content.intersphinx')

from giza.command import command
from giza.serialization import ingest_yaml_list
from giza.files import verbose_remove

ACCEPTABLE = 864000

#### Helper functions

def download_file(file, url):
    cmd = ['curl', '-s', '--remote-time', url, '-o', file]
    command(' '.join(cmd))
    logger.info('downloaded {0}'.format(file))

def file_timestamp(path):
    return os.stat(path)[8]

#### Tasks

def download(f, s):
    if os.path.isfile(f):
        newf = False
    else:
        logger.info('{0} file does not exist, downloading now'.format(f))
        newf = download_file(f, s)

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

def intersphinx_tasks(conf, app):
    if 'intersphinx' not in conf.system.files.data:
        return

    for i in conf.system.files.data.intersphinx:
        try:
            f = os.path.join(conf.paths.projectroot,
                             conf.paths.output, i.path)

            s = i.url + 'objects.inv'
        except AttributeError:
            f = os.path.join(conf.paths.projectroot,
                             conf.paths.output, i['path'])

            s = i['url'] + 'objects.inv'

        t = app.add('task')

        t.target = f
        t.job = download
        t.args = { 'f': f, 's': s }
        t.description = 'download intersphinx inventory from {0}'.format(s)

        logger.debug('added job for {0}'.format(s))

def intersphinx_clean(conf, app):
    for inv in conf.system.files.data.intersphinx:
        try:
            fn = os.path.join(conf.paths.projectroot,
                              conf.paths.output, inv.path)
        except AttributeError:
            fn = os.path.join(conf.paths.projectroot,
                              conf.paths.output, inv['path'])


        if os.path.exists(fn):
            t = app.add('task')
            t.job = verbose_remove
            t.args = [fn]
