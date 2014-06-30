import logging

logger = logging.getLogger('giza.app')

from giza.pool import ThreadPool, ProcessPool, SerialPool, WorkerPool
from giza.config.main import Configuration

from giza.task import Task, MapTask

class BuildApp(object):
    def __init__(self, conf):
        self.conf = conf
        self.queue = []
        self.results = []
        self.worker_pool = None
        self.default_pool = self.conf.runstate.runner
        self.needs_rebuild = True
        self.root_app = True

    @property
    def worker_pool(self):
        if self._worker_pool is None:
            self.pool = None
        return self._worker_pool

    @worker_pool.setter
    def worker_pool(self, value):
        self._worker_pool = value

    @property
    def pool(self):
        if self.worker_pool is None:
            self.pool = None

        return self.worker_pool

    @pool.setter
    def pool(self, value=None):
        if value is not None and self.is_pool(self.worker_pool):
            self.close_pool()

        if self.is_pool(value) or isinstance(value, SerialPool):
            self.worker_pool = value
            return

        if (value is not None and
            self.default_pool != value and
            self.is_pool_type(value)):
            self.default_pool = value

        if self.default_pool == 'thread':
            self.worker_pool = ThreadPool(self.conf)
        elif self.default_pool == 'process':
            self.worker_pool = ProcessPool(self.conf)
        elif self.default_pool == 'serial':
            self.worker_pool = SerialPool(self.conf)

    @staticmethod
    def is_pool(pool):
        if isinstance(pool, (WorkerPool, SerialPool)):
            return True
        else:
            return False

    @staticmethod
    def is_pool_type(value):
        if value in ('thread', 'process', 'serial'):
            return True
        else:
            return False

    def close_pool(self):
        if self.is_pool(self.worker_pool) and not isinstance(self.worker_pool, SerialPool):
            self._worker_pool.p.close()
            self._worker_pool.p.join()
            self._worker_pool = None

    def add(self, task=None):
        if task is None or task in (Task, 'task'):
            t = Task()
            t.conf = self.conf
            self.queue.append(t)
            return t
        elif task in (MapTask, 'map'):
            t = MapTask()
            t.conf = self.conf
            self.queue.append(t)
            return t
        elif task in (BuildApp, 'app'):
            t = BuildApp(self.conf)
            t.root_app = False
            self.queue.append(t)
            return t
        else:
            if isinstance(task, Task):
                if t.conf is None:
                    task.conf = self.conf

                self.queue.append(task)
                return task
            elif isinstance(task, BuildApp):
                task.root_app = False
                self.queue.append(task)
                return task
            else:
                raise TypeError('invalid task type')

    def run(self):
        if len(self.queue) == 1:
            j = self.queue[0]
            if isinstance(j, BuildApp):
                self.results.extend(j.run())
            elif isinstance(j, Task):
                self.results.append(j.run())
            else:
                raise TypeError
        elif len([ t for t in self.queue if isinstance(t, BuildApp)]) >= 1:
            group = [ ]
            self.pool = None
            for task in self.queue:
                if not isinstance(task, BuildApp):
                    group.append(task)
                else:
                    if len(group) == 1:
                        j = group[0]
                        self.results.append(j.run())
                        group = []
                    elif len(group) > 1:
                        self.results.extend(self.pool.runner(group))
                        group = []

                    if task.worker_pool is None:
                        task.pool = self.pool

                    self.results.append(task.run())

            if len(group) != 0:
                self.results.extend(self.pool.runner(group))
        else:
            self.results.extend(self.pool.runner(self.queue))
