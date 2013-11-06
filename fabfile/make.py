import datetime
import json
import os

from multiprocessing import cpu_count, Pool

from fabric.api import lcd, local, task, env

from docs_meta import get_conf
from utils import md5_file, expand_tree

env.FORCE = False
@task
def force():
    env.FORCE = True

env.PARALLEL = True
@task
def serial():
    env.PARALLEL = False

env.POOL = None
@task
def pool(value):
    env.POOL = int(value)

@task
def make(target):
    return _make(target)

def _make(target):
    with lcd(get_conf().build.paths.projectroot):
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
        if not fn.startswith(conf.build.paths.projectroot):
            if fn.startswith(conf.build.paths.source):
                fn = os.path.join(conf.build.paths.projectroot, fn)
            if fn.startswith('/'):
                fn = os.path.join(conf.build.paths.projectroot,
                                  conf.build.paths.source,
                                  fn[1:])

        return fn

    def needs_rebuild(t, d):
        if d in dep_map:
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

    files = expand_tree(os.path.join(conf.build.paths.projectroot, conf.build.paths.source), None)

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

def runner(jobs, pool=None, retval='count'):
    if pool == 1 or env.PARALLEL is False:
        return sync_runner(jobs, env.FORCE, retval)
    else:
        if pool is None:
            pool = cpu_count()

        return async_runner(jobs, env.FORCE, pool, retval)

def async_runner(jobs, force, pool, retval):
    try:
        p = Pool()
    except:
        print('[ERROR]: can\'t start pool, falling back to sync ')
        return sync_runner(jobs, force, retval)

    count = 0
    results = []

    for job in jobs:
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

            count += 1

    p.close()
    p.join()

    if retval == 'count':
        return count
    elif retval is None:
        return None
    elif retval == 'results':
        return [ o.get() for o in results ]
    else:
        return dict(count=count,
                    results=[ o.get() for o in results ])

def sync_runner(jobs, force, retval):
    count = 0
    results = []

    for job in jobs:
        if force is True or check_dependency(job['target'], job['dependency']):
            if isinstance(job['args'], dict):
                r = job['job'](**job['args'])
            else:
                r = job['job'](*job['args'])

            results.append(r)
            if 'callback' in job:
                job['callback'](r)

            count +=1

    if retval == 'count':
        return count
    elif retval is None:
        return None
    elif retval == 'results':
        return results
    else:
        return dict(count=count,
                    results=results)
