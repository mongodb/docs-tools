import multiprocessing.dummy

from multiprocessing import cpu_count

try:
    from utils.jobs.dependency import check_dependency
    from utils.jobs.pool import NestedPool
    from utils.jobs.errors import PoolResultsError, JobRunnerError
except ImportError:
    from dependency import check_dependency
    from pool import NestedPool
    from errors import PoolResultsError, JobRunnerError

def runner(jobs, pool, parallel, force, retval=True):
    if parallel is False:
        results = sync_runner(jobs, force)
    elif parallel is True or parallel == 'process':
        results = async_process_runner(jobs, force, pool)
    elif parallel.startswith('threads'):
        results = async_thread_runner(jobs, force, pool)
    else:
        raise JobRunnerError

    if retval == 'count':
        return len(results)
    elif retval is None:
        return None
    else:
        return results

def async_thread_runner(jobs, force, pool):
    try:
        p = multiprocessing.dummy.Pool(pool)
    except:
        print('[ERROR]: can\'t start pool, falling back to sync ')
        return sync_runner(jobs, force)

    return async_runner(jobs, force, pool, p)

def async_process_runner(jobs, force, pool):
    try:
        p = NestedPool(pool)
    except:
        print('[ERROR]: can\'t start pool, falling back to sync ')
        return sync_runner(jobs, force)

    return async_runner(jobs, force, pool, p)


def async_runner(jobs, force, pool, p):
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

    if force is False:
        retval = []
        has_errors = False

        for ret in results:
            try:
                retval.append(ret.get())
            except Exception as e:
                has_errors = True
                print(e)

        if has_errors is True:
            raise PoolResultsError
        else:
            results = retval
    else:
        results = [ o.get() for o in results ]

    return results

def sync_runner(jobs, force):
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

    return results

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
