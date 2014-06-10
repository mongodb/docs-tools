import time
import os
import logging

logger = logging.getLogger(os.path.basename(__file__))

from giza.tools.serialization import ingest_yaml_list
from giza.tools.shell import command

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
    data_file = os.path.join(conf.paths.projectroot,
                             conf.paths.builddata,
                             'intersphinx.yaml')

    if not os.path.exists(data_file):
        return

    intersphinx_mapping = ingest_yaml_list(data_file)

    for i in intersphinx_mapping:
        f = os.path.join(conf.paths.projectroot,
                         conf.paths.output, i['path'])

        s = i['url'] + 'objects.inv'

        t = app.add('task')

        t.target = f
        t.job = download
        t.args = { 'f': f, 's': s }
        t.description = 'download intersphinx inventory from {0}'.format(s)

        logger.info('added job for {0}'.format(s))
