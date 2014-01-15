import multiprocessing.dummy

from utils.jobs.pool import NestedPool

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
