import multiprocessing.dummy

try:
    from utils.jobs.dependency import check_dependency
    from utils.jobs.pool import NestedPool
    from utils.jobs.errors import PoolResultsError, JobRunnerError
except ImportError:
    from dependency import check_dependency
    from pool import NestedPool
    from errors import PoolResultsError, JobRunnerError

def runner(jobs, pool, parallel, force, retval):
    if parallel is False:
        return sync_runner(jobs, force, retval)
    elif parallel is True or parallel == 'process':
        return async_process_runner(jobs, force, pool, retval)
    elif parallel.startswith('threads'):
        return async_thread_runner(jobs, force, pool, retval)
    else:
        raise JobRunnerError

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

    if retval == 'count':
        return len(results)
    elif retval is None:
        return None
    elif retval == 'results':
        return results
    else:
        return dict(count=len(results),
                    results=results)

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
