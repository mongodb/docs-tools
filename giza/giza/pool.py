import multiprocessing
import multiprocessing.dummy
import logging
import os.path

logger = logging.getLogger(os.path.basename(__file__))

from giza.task import Task

class PoolResultsError(Exception):
    pass

def run_task(task):
    "helper to call run method on task so entire operation can be pickled for process pool support"

    return task.run()

class WorkerPool(object):
    def __enter__(self):
        return self.p

    def __exit__(self, *args):
        self.p.close()
        self.p.join()

    def runner(self, jobs):
        return self.get_results(self.async_runner(jobs))

    def async_runner(self, jobs):
        results = []

        if len(jobs) == 1:
            results.append((jobs[0], jobs[0].run()))
        else:
            for job in jobs:
                if not hasattr(job, 'run'):
                    raise TypeError('task "{0}" is not a valid Task'.format(job))

                if job.needs_rebuild is True:
                    results.append((job, self.p.apply_async(run_task, args=[job])))
                else:
                    logger.debug("{0} does not need a rebuild".format(job.target))

        return results

    def get_results(self, results):
        has_errors = False

        retval = []
        errors = []

        for job, ret in results:
            try:
                if ret is None:
                    retval.append(ret)
                else:
                    retval.append(ret.get())
            except Exception as e:
                has_errors = True
                errors.append((job, e))

        if has_errors is True:
            error_list = []
            for job, err in errors:
                error_list.append(e)
                if job.description is None:
                    logger.error("encountered error '{0}' in {1} with args ({2})".format(e, job.job, job.args))
                else:
                    logger.error("'{0}' encountered error: {1}, exiting.".format(job.description, e))

            raise PoolResultsError(error_list)

        return retval

class SerialPool(object):
    def __init__(self, conf=None):
        self.p = None
        self.conf = conf
        logger.debug('new phony "serial" pool object')

    def get_results(self, results):
        return results

    def runner(self, jobs):
        results = []
        for job in jobs:
            results.append(job.run())

        return results

    async_runner = runner

class ThreadPool(WorkerPool):
    def __init__(self, conf=None):
        self.p = multiprocessing.dummy.Pool()
        self.conf = conf
        logger.debug('new thread pool object')

class ProcessPool(WorkerPool):
    def __init__(self, conf=None):
        self.conf = conf
        self.p = multiprocessing.Pool()
        logger.debug('new process pool object')
