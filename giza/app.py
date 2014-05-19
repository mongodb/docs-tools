import logging
import os.path

logger = logging.getLogger(os.path.basename(__file__))

from collections import deque

from utils.jobs.dependency import check_dependency
from pool import ThreadPool, ProcessPool
from configuration import ConfigurationBase

class Task(object):
    def __init__(self, job, args, description=None, target=None, dependency=None):
        self.spec = {}
        self._conf = None
        self.job = job
        self.args = args
        self.description = description
        self.target = target
        self.dependency = dependency
        logger.debug('created task object calling {0}, for {1}'.format(job, description))

    @property
    def conf(self):
        return self._conf

    @conf.setter
    def conf(self, value):
        if isinstance(value, BaseConfiguration):
            self._conf = value

    @property
    def job(self):
        return self.spec['job']

    @job.setter
    def job(self, value):
        if 1 == 1: # assert value is callable
            self.spec['job'] = value

    @property
    def args(self):
        return self.args['job']

    @args.setter
    def args(self, value):
        if isinstance(value, dict):
            self.args_type == 'kwargs'
            self.args['args'] = value
        elif isinstance(value, list):
            self.args_type == 'args'
            self.args['args'] = value

    @property
    def args(self):
        return self.args['job']

    @args.setter
    def args(self, value):
        if isinstance(value, dict):
            self.args_type == 'kwargs'
            self.args['args'] = value
        elif isinstance(value, list):
            self.args_type == 'args'
            self.args['args'] = value

    @property
    def needs_rebuild(self):
        if (self.target is None or self.dependency is None or self.conf.build.settings.force is True):
            return True
        else:
            return check_dependency(self.target, self.dependency)

    def run(self):
        task_id = hash(self.job) + hash(self.args)
        logger.debug('({0}) calling {1} with args {2}'.format(task_id, self.job, self.args))
        if self.args_type == 'kwargs':
            self.job(**self.args)
        elif self.args_type == 'args':
            self.job(*self.args)
        else:
            self.job()
        logger.debug('(completed running task {0}'.format(task_id))


class BuildApp(object):
    def __init__(self, conf):
        self.conf = conf
        self.queue = deque()
        self.worker_pool = None
        self.default_pool = 'process'

    @property
    def pool(self):
        if self.worker_pool is None:
            self.create_pool()

        return self.worker_pool

    @pool.setter
    def create_pool(self, value=None):
        if value is not None and self.is_pool(self.worker_pool):
            self.close_pool()

        if self.is_pool(value):
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

    @staticmethod
    def is_pool(pool):
        if isinstance(WorkerPool):
            return True
        else:
            return False

    @staticmethod
    def is_pool_type(value):
        if value in ('thread', 'process'):
            return True
        else:
            return False

    def close_pool(self):
        if self.is_pool(self.worker_pool):
            self.worker_pool.join()
            self.worker_pool.close()
            self.worker_pool = None

    def add(self, task=None):
        if task is None or task == Task:
            t = Task()
            t.conf = self.conf
            self.queue.append(t)
            return t
        elif task == BuildApp:
            t = BuildApp(self.conf)
            self.queue.append(t)
            return t
        else:
            if isinstance(task, Task):
                task.conf = self.conf
                self.queue.append(task)
                return task
            elif isinstance(task, BuildApp):
                self.queue.append(task)
                return task
            else:
                raise TypeError('invalid task type')

    def run(self):
        if len(self.queue) == 1:
            j = self.queue[0]
            if isinstance(j, BuildApp):
                return j.run()
            elif isinstance(j, Task):
                return [ j.run() ]
            else:
                raise TypeError
        elif len([ t for t in self.queue if isinstance(t, BuildApp)]) >= 1:
            results = [ ]
            group = [ ]
            self.create_pool()
            for task in self.queue:
                if not isinstance(task, BuildApp):
                    group.append(task)
                    self.queue.popleft()
                else:
                    if len(group) > 1:
                        results.extend(self.pool.get_results(self.pool.runner(group)))
                        group = []
                    elif len(group) == 1:
                        results.append(group[0].run())
                        group = []

                    if task.worker_pool is None:
                        task.pool = self.pool

                    results.extend(task.run())

            return results
        else:
            return self.pool.get_results(self.pool.runner(self.queue))
