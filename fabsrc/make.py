import datetime
import json
import os

import multiprocessing
import multiprocessing.pool
import multiprocessing.dummy

from multiprocessing import cpu_count

from fabric.api import lcd, local, task, env

from docs_meta import get_conf
from utils import md5_file, expand_tree

env.FORCE = False
@task
def force():
    "Sets a flag that forces rebuilds of all generated and processed content."

    env.FORCE = True

env.PARALLEL = True
@task
def serial():
    "Sets a flag that removes parallelism from the build process."

    env.PARALLEL = False

env.POOL = None
@task
def pool(value):
    "Manually control the size of the worker pool."

    env.POOL = int(value)

@task
def make(target):
    "Build a make target, indirectly."

    return _make(target)

def _make(target):
    conf = get_conf()
    with lcd(conf.paths.projectroot):
        if isinstance(target, list):
            target_str = make + ' '.join([target])
        elif isinstance(target, basestring):
            target_str = ' '.join(['make', target])

        local(target_str)

############### Hashed Dependency Checking ###############

def check_hashed_dependency(target, dependency, dep_map, conf=None):
    if conf is None:
        conf = get_conf()

    def normalize_fn(fn):
        if not fn.startswith(conf.paths.projectroot):
            if fn.startswith(conf.paths.source):
                fn = os.path.join(conf.paths.projectroot, fn)
            if fn.startswith('/'):
                fn = os.path.join(conf.paths.projectroot,
                                  conf.paths.source,
                                  fn[1:])

        return fn

    def needs_rebuild(t, d):
        if dep_map is None:
            return check_dependency(t, d)
        elif d in dep_map:
            fn_hash = md5_file(d)
        else:
            return check_dependency(t, d)

        if dep_map[d] == fn_hash:
            return False
        else:
            return True

    if target is None or dependency is None:
        return True

    if isinstance(target, list):
        target = [ normalize_fn(t) for t in target ]
        for f in target:
            if not os.path.exists(f):
                return True
    else:
        target = normalize_fn(target)
        if not os.path.exists(target):
            return True

    if isinstance(dependency, list):
        dependency = [ normalize_fn(d) for d in dependency ]
        for dep in dependency:
            if needs_rebuild(target, dep) is True:
                return True
        return False
    else:
        dependency = normalize_fn(dependency)
        return needs_rebuild(target, dependency)

def dump_file_hashes(output, conf=None):
    if conf is None:
        conf = get_conf()

    o = { 'conf': conf,
          'time': datetime.datetime.utcnow().strftime("%s"),
          'files': { }
        }

    files = expand_tree(os.path.join(conf.paths.projectroot, conf.paths.source), None)

    fmap = o['files']

    for fn in files:
        fmap[fn] = md5_file(fn)

    output_dir = os.path.dirname(output)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output, 'w') as f:
        json.dump(o, f)

    print('[build]: wrote dependency cache to: {0}'.format(output))

############### Dependency Checking ###############

def check_three_way_dependency(target, source, dependency):
    if not os.path.exists(target):
        # if .json doesn't exist, rebuild
        return True
    else:
        dep_mtime = os.stat(dependency).st_mtime
        if os.stat(source).st_mtime > dep_mtime:
            # if <file>.txt is older than <file>.fjson,
            return True
        elif dep_mtime > os.stat(target).st_mtime:
            #if fjson is older than json
            return True
        else:
            return False

def check_dependency(target, dependency):
    if dependency is None:
        return True

    if isinstance(target, list):
        return check_multi_dependency(target, dependency)

    if not os.path.exists(target):
        return True

    def needs_rebuild(targ_t, dep_f):
        if targ_t < os.stat(dep_f).st_mtime:
            return True
        else:
            return False

    target_time = os.stat(target).st_mtime
    if isinstance(dependency, list):
        ret = False
        for dep in dependency:
            if needs_rebuild(target_time, dep):
                ret = True
                break
        return ret
    else:
        return needs_rebuild(target_time, dependency)

def check_multi_dependency(target, dependency):
    for t in target:
        if check_dependency(t, dependency) is True:
            return True

    return False

############### Task Running Framework ###############

##### Permit Nested Pool #####

class NonDaemonProcess(multiprocessing.Process):
    def _get_daemon(self):
        return False
    def _set_daemon(self, value):
        pass
    daemon = property(_get_daemon, _set_daemon)

class NestedPool(multiprocessing.pool.Pool):
    Process = NonDaemonProcess

############### Task Running Framework ###############

def runner(jobs, pool=None, parallel='process', force=False, retval='count'):
    if pool is None:
        pool = cpu_count()

    if env.FORCE is True:
        force = True
    if env.PARALLEL is False:
        parallel = False

    if pool == 1 or parallel is False:
        return sync_runner(jobs, force, retval)
    elif parallel is True or parallel == 'process':
        return async_process_runner(jobs, force, pool, retval)
    elif parallel.startswith('threads'):
        return async_thread_runner(jobs, force, pool, retval)

def async_thread_runner(jobs, force, pool, retval):
    try:
        p = multiprocessing.dummy.Pool(pool)
    except:
        print('[ERROR]: can\'t start pool, falling back to sync ')
        return sync_runner(jobs, force, retval)

    return async_runner(jobs, force, pool, retval, p)

def async_process_runner(jobs, force, pool, retval):
    try:
        p = NestedPool(pool)
    except:
        print('[ERROR]: can\'t start pool, falling back to sync ')
        return sync_runner(jobs, force, retval)

    return async_runner(jobs, force, pool, retval, p)

def async_runner(jobs, force, pool, retval, p):
    results = []

    for job in jobs:
        if 'target' not in job:
            job['target'] = None
        if 'dependency' not in job:
            job['dependency'] = None

        if force is True or check_dependency(job['target'], job['dependency']):
            if 'callback' in job:
                if isinstance(job['args'], dict):
                    results.append(p.apply_async(job['job'], kwds=job['args'], callback=job['callback']))
                else:
                    results.append(p.apply_async(job['job'], args=job['args'], callback=job['callback']))
            else:
                if isinstance(job['args'], dict):
                    results.append(p.apply_async(job['job'], kwds=job['args']))
                else:
                    results.append(p.apply_async(job['job'], args=job['args']))

    p.close()
    p.join()

    if retval == 'count':
        return len(results)
    elif retval is None:
        return None
    elif retval == 'results':
        return [ o.get() for o in results ]
    else:
        return dict(count=len(results),
                    results=[ o.get() for o in results ])

def sync_runner(jobs, force, retval):
    results = []

    for job in jobs:
        if 'target' not in job:
            job['target'] = None
        if 'dependency' not in job:
            job['dependency'] = None

        if force is True or check_dependency(job['target'], job['dependency']):
            if isinstance(job['args'], dict):
                r = job['job'](**job['args'])
            else:
                r = job['job'](*job['args'])

            results.append(r)
            if 'callback' in job:
                job['callback'](r)

    if retval == 'count':
        return len(results)
    elif retval is None:
        return None
    elif retval == 'results':
        return results
    else:
        return dict(count=len(results),
                    results=results)

def mapper(func, iter, pool=None, parallel='process'):
    if pool is None:
        pool = cpu_count()
    elif pool == 1:
        return map(func, iter)

    if parallel in ['serial', 'single']:
        return map(func, iter)
    else:
        if parallel == 'process':
            p = NestedPool(pool)
        elif parallel.startswith('thread'):
            p = multiprocessing.dummy.Pool(pool)
        else:
            return map(func, iter)

    result = p.map(func, iter)

    p.close()
    p.join()

    return result

def resolve_dict_keys(dict):
    return { k:v.get() for k,v in dict.items() }

def resolve_results(results):
    return [ r.get() for r in results ]

class WorkerPool(object):
    def __exit__(self, *args):
        self.p.close()
        self.p.join()

class ThreadPool(WorkerPool):
    def __enter__(self):
        self.p = multiprocessing.dummy.Pool()
        return self.p

class ProcessPool(WorkerPool):
    def __enter__(self):
        self.p = NestedPool()
        return self.p
