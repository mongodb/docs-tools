# Copyright 2014 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

        self.pool_mapping = {
            'thread': ThreadPool,
            'process': ProcessPool,
            'serial': SerialPool
        }
        self.pool_types = tuple([ self.pool_mapping[p] for p in self.pool_mapping ])

        self.needs_rebuild = True
        self.root_app = True

    @property
    def pool(self):
        if self.worker_pool is None:
            self.create_pool()

        return self.worker_pool

    @pool.setter
    def pool(self, value=None):
        self.create_pool(value)

    def create_pool(self, pool=None):
        if pool is None:
            if self.worker_pool is None:
                pool = self.default_pool
            else:
                pool = self.worker_pool

        if self.worker_pool is not None:
            logger.debug('not creating a pool because one already exists. ({0}, {1})'.format(pool, type(pool)))
            return

        if isinstance(self.worker_pool, self.pool_mapping[self.default_pool]):
            return
        elif self.worker_pool is None:
            if self.is_pool(pool) and self.worker_pool is None:
                self.worker_pool = pool
            elif self.is_pool_type(pool) and self.worker_pool is None:
                self.worker_pool = self.pool_mapping[pool](self.conf)
            else:
                self.worker_pool = self.pool_mapping[self.default_pool](self.conf)
        else:
            raise TypeError("pool {0} of type {1} is invalid".format(pool, type(pool)))

    def is_pool(self, pool):
        if isinstance(pool, self.pool_types):
            return True
        else:
            return False

    def is_pool_type(self, value):
        if value in self.pool_mapping:
            return True
        else:
           return False

    @property
    def queue_has_apps(self):
        if len(self.queue) <= 1:
            return False
        elif len(self.queue) >= 2:
            num_apps = len([ t for t in self.queue if isinstance(t, BuildApp)])
            if num_apps == 0:
                return False
            elif num_apps >= 1:
                return True
        else:
            return False

    def close_pool(self):
        if self.is_pool(self.worker_pool) and not isinstance(self.worker_pool, SerialPool):
            self.worker_pool.close()
            self.worker_pool = None

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
            self.create_pool()
            t = BuildApp(self.conf)
            t.pool = self.pool
            t.root_app = False
            self.queue.append(t)
            return t
        else:
            if isinstance(task, Task):
                if task.conf is None:
                    task.conf = self.conf

                self.queue.append(task)
                return task
            elif isinstance(task, BuildApp):
                self.create_pool()
                task.root_app = False
                task.pool = self.pool
                self.queue.append(task)
                return task
            else:
                raise TypeError('invalid task type')

    def _run_single(self, j):
        if isinstance(j, BuildApp):
            if j.pool is None:
                j.pool = self.pool

            self.results.extend(j.run())
        elif isinstance(j, Task):
            self.results.append(j.run())
        else:
            raise TypeError

    def _run_mixed_queue(self):
        group = [ ]

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

                if task.pool is None:
                    task.pool = self.pool

                if isinstance(task, Task):
                    self.results.append(task.run())
                else:
                    self.results.extend(task.run())

        if len(group) != 0:
            self.results.extend(self.pool.runner(group))

    def run(self):
        if len(self.queue) == 1:
            self._run_single(self.queue[0])
        elif self.queue_has_apps is True:
            self._run_mixed_queue()
        else:
            self.results.extend(self.pool.runner(self.queue))

        self.queue = []
        return self.results
