import logging
import os.path
import multiprocessing.dummy
from multiprocessing import cpu_count

logger = logging.getLogger(os.path.basename(__file__))

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
    elif parallel.startswith('thread'):
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
        logger.warning(' can\'t start pool, falling back to synchronous pool.')
        return sync_runner(jobs, force)

    return async_runner(jobs, force, pool, p)

def async_process_runner(jobs, force, pool):
    try:
        p = NestedPool(pool)
    except:
        logger.warning(' can\'t start pool, falling back to synchronous pool.')
        return sync_runner(jobs, force)

    return async_runner(jobs, force, pool, p)

def async_job_loop(jobs, force, p):
    results = []

    for job in jobs:

        if 'target' not in job:
            job['target'] = None
        if 'dependency' not in job:
            job['dependency'] = None

        if force is True or check_dependency(job['target'], job['dependency']):
            if 'callback' in job:
                if isinstance(job['args'], dict):
                    r = p.apply_async(job['job'], kwds=job['args'], callback=job['callback'])
                else:
                    r = p.apply_async(job['job'], args=job['args'], callback=job['callback'])
            else:
                if isinstance(job['args'], dict):
                    r = p.apply_async(job['job'], kwds=job['args'])
                else:
                    r = p.apply_async(job['job'], args=job['args'])

            results.append( ( job, r ) )

    return results

def process_async_results(results, force):
    if force is False:
        retval = []
        has_errors = False

        errors = []
        for job, ret in results:
            try:
                retval.append(ret.get())
            except Exception as e:
                has_errors = True
                errors.append((job, e))

        if has_errors is True:
            error_list = []
            for job, e in errors:
                error_list.append(e)
                if 'description' in job:
                    logger.error("'{0}' encountered error: {1}, exiting.".format(job['description'], e))
                else:
                    logger.error("encountered error in {0} with args ({1})".format(job['job'], job['args']))

            raise PoolResultsError(error_list)
        else:
            results = retval
    else:
        results = [ o.get() for job, o in results ]

    return results

def async_runner(jobs, force, pool, p):
    results = async_job_loop(jobs, force, p)

    p.close()
    p.join()

    return process_async_results(results, force)

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

            if 'callback' in job:
                job['callback'](r)

            results.append( (job, r ) )

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
