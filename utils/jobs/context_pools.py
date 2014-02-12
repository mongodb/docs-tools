import multiprocessing.dummy

from utils.jobs.pool import NestedPool
from utils.jobs.pool import NestedPool
from utils.jobs.runners import async_job_loop, process_async_results

class WorkerPool(object):
    def __exit__(self, *args):
        self.p.close()
        self.p.join()

    def runner(self, jobs, force=False, pool=None, p=None):
        results = async_job_loop(jobs, force, self.p)

        return process_async_results(results, force)

class ThreadPool(WorkerPool):
    def __enter__(self):
        self.p = multiprocessing.dummy.Pool()
        self.p.runner = self.runner

        return self.p

class ProcessPool(WorkerPool):
    def __enter__(self):
        self.p = NestedPool()
        self.p.runner = self.runner

        return self.p
