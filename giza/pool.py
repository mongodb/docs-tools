import multiprocessing
import logging
import os.path

logger = logging.getLogger(os.path.basename(__file__))

class WorkerPool(object):
    def __enter__(self):
        return self.p

    def __exit__(self, *args):
        self.p.close()
        self.p.join()

    def runner(self, jobs):
        results = []
        if len(jobs) == 1:
            results.append((job, jobs[0].run()))

        for job in jobs:
            if not isinstance(Task):
                raise TypeError('task "{0}" is not a valid Task'.format(job))

            if job.needs_rebuild is True:
                results.append((job, self.p.apply_async(job.run)))

        logger.debug('all tasks running in a worker pool')
        return results

    def get_results(self, results):
        has_errors = False

        retval = []
        errors = []

        for job, ret in results:
            try:
                retval.append(ret.get())
            except Exception as e:
                has_errors = True
                errors.append((job, e))

        if has_errors is True:
            error_list = []
            for job, err in errors:
                error_list.append(e)
                if job.description is None:
                    logger.error("encountered error {0} in {1} with args ({2})".format(e, job.job, job.args))
                else:
                    logger.error("'{0}' encountered error: {1}, exiting.".format(job.description, e))

            raise PoolResultsError(error_list)

        return retval

class ThreadPool(WorkerPool):
    def __init__(self, conf=None):
        self.p = multiprocessing.dummy.pool.Pool()
        self.conf = conf
        logger.debug('new thread pool object')

class ProcessPool(WorkerPool):
    def __init__(self):
        self.p = multiprocessing.Pool()
        logger.debug('new process pool object')
