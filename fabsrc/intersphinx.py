import sys
import os
import time
from multiprocessing import Pool

from fabric.api import task, local, env, puts, hide
from fabric.utils import _AttributeDict as ad
from docs_meta import get_conf
from utils import ingest_yaml_list

from make import runner

ACCEPTABLE = 864000
env.msgid = 'intersphinx'

#### Helper functions

def download_file(file, url):
    cmd = ['curl', '-s', '--remote-time', url, '-o', file]
    with hide('running'):
        local(' '.join(cmd))

def file_timestamp(path):
    return os.stat(path)[8]

#### Tasks

def download(f, s):
    if os.path.isfile(f):
        newf = False
    else:
        puts('[intersphinx]: "{0} file does not exist'.format(f))
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

def intersphinx():
    "Downloads all intersphinx files if out of date."

    count = runner( intersphinx_jobs() )

    puts('[intersphinx]: processed {0} intersphinx inventories'.format(count))

def intersphinx_jobs():
    conf = get_conf()
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
        yield {
                'target': f,
                'dependency': None,
                'job': download,
                'args': { 'f': f, 's': s }
              }
