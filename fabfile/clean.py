from fabric.api import task, abort
import time
import os
import sys
import shutil

import utils
import docs_meta
from multiprocessing import Pool, cpu_count

def _rm_rf(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)

@task
def builds(days=14):
    days = time.time() - 60*60*24 * int(days)

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../build/')) + '/'

    builds = [ path + o for o in os.listdir(path) if os.path.isdir(path + o)]

    for build in builds:
        branch = build.rsplit('/', 1)[1]

        if branch in docs_meta.conf.git.branches.published:
            continue
        elif branch == docs_meta.get_branch:
            continue
        elif branch == 'public':
            continue
        elif os.stat(build).st_mtime < days:
            _rm_rf(build)
            _rm_rf(path + "public/" + branch)
            print('[clean]: removed stale build artifact: ' + build)

def _multi_clean(paths):
    if len(paths) <= cpu_count + 1:
        workers = len(paths)
    else:
        workers = cpu_count

    p = Pool(workers)

    for i in paths:
        p.apply_async(_rm_rf, args=(i))

    p.close()
    p.join()


@task
def toc():
    if not env.FORCE:
        abort('[clean]: cannot clean without calling ``force`` task.')



@task
def tables():
    if not env.FORCE:
        abort('[clean]: cannot clean without calling ``force`` task.')

@task
def api():
    if not env.FORCE:
        abort('[clean]: cannot clean without calling ``force`` task.')
