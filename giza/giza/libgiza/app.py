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

"""
:mod:`app` holds the :class:`~giza.app.BuildApp()` class that provides an
organizing framework for running larger sequences of operations.
"""

import collections
import contextlib
import logging
import random
import numbers

import giza.libgiza.pool

from giza.libgiza.task import Task, MapTask
from giza.libgiza.config import ConfigurationBase

logger = logging.getLogger('giza.libgiza.app')


class BuildApp(object):
    """
    A unit of work. :class:`~giza.app.BuildApp()` instances possess queues of
    :class:`~giza.task.Task()` objects and sub-\ :class:`~giza.app.BuildApp()`
    objects that describe a build process. Groups of :class:`~giza.task.Task()`
    objects may execute in parallel, while any :class:`~giza.app.BuildApp()`
    objects in the queue execute in isolation after proceeding group of
    :class:`~giza.task.Task()` operations complete. Mix
    :class:`~giza.app.BuildApp()` and :class:`~giza.task.Task()` operations to
    control task ordering.

    The results of all operations are accessible in the
    :attr:`~giza.app.BuildApp.results`, which largely preserves the ordering of
    the insertion of operations into the queue. Unlike the queue,
    :attr:`~giza.app.BuildApp.results` contains the result of each operation in
    an embedded :class:`~giza.app.BuildApp()` in the order that each task was
    added to the embedded :class:`~giza.app.BuildApp()` instance.

    :class:`~giza.app.BuildApp()` are reusable: after running all operations in
    the queue, the queue resets. However, results do not reset.
    """

    def __init__(self, conf=None, force=False):
        """
        :param ConfigurationBase conf: A top level
           ``Configuration`` object.
        """

        self._conf = conf
        self._force = force
        self._default_pool = 'lazy'
        self._pool_size = None

        self.queue = []
        self.results = []
        self.worker_pool = None
        self._randomize = False

        self.pool_mapping = {
            'thread': giza.libgiza.pool.ThreadPool,
            'process': giza.libgiza.pool.ProcessPool,
            'event': giza.libgiza.pool.EventPool,
            'serial': giza.libgiza.pool.SerialPool
        }

        self.pool_types = tuple(self.pool_mapping.values())

        # so that apps are compatible with tasks in pools
        self.needs_rebuild = True
        self.finalizers = []

        self.root_app = True

        self.target = None
        self.dependency = None

    @classmethod
    def new(cls, pool_type='process', pool_size=None, force=False):
        app = cls()
        app.force = force
        app.default_pool = pool_type
        app.pool_size = pool_size

        return app

    @property
    def dependency(self):
        return self._dependency

    @dependency.setter
    def dependency(self, value):
        self._dependency = value

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    @property
    def description(self):
        jobs = str([j.job if isinstance(j, Task) else type(j)
                    for j in self.queue])

        if self.root_app is True:
            return "a root level BuildApp object: " + jobs
        else:
            return "a BuildApp member BuildApp object: " + jobs

    @property
    def force(self):
        if self._force is None:
            if self.conf is None:
                self._force = False
            else:
                logger.warning('deprecated use of conf object in app setup for force value')
                self._force = self.conf.runstate.force

        return self._force

    @force.setter
    def force(self, value):
        self._force = bool(value)

    @property
    def pool_size(self):
        if self._pool_size is None:
            if self.conf is None:
                # the pool objects themselves know what to do, and so we don't
                # need to over-define defaults here.
                return None
            else:
                logger.warning('deprecated use of conf object for setting pool size')
                self.pool_size = self.conf.runstate.pool_size

        return self._pool_size

    @pool_size.setter
    def pool_size(self, value):
        if isinstance(value, numbers.Number):
            self._pool_size = value
        else:
            logger.warning('{0} is an invalid pool size'.format(str(value)))

    @property
    def conf(self):
        return self._conf

    @conf.setter
    def conf(self, value):
        if isinstance(value, ConfigurationBase):
            self._conf = value

    @property
    def randomize(self):
        return self._randomize

    @randomize.setter
    def randomize(self, value):
        if isinstance(value, bool):
            self._randomize = value
        else:
            self._randomize = bool(value)

    @property
    def default_pool(self):
        if self._default_pool is None:
            if self.conf is None:
                logger.warning('pool type not specified, choosing at random')
                self.default_pool = 'random'
            else:
                logger.warning('deprecated use of conf object in app setup for pool type')
                self._default_pool = self.conf.runstate.runner

        if self.root_app is True and self._default_pool in (None, 'lazy'):
            self.default_pool = 'random'

        return self._default_pool

    @default_pool.setter
    def default_pool(self, value):
        if value == 'lazy':
            pass
        elif value == 'random':
            self._default_pool = random.choice(['process', 'thread', 'serial'])
        elif value in self.pool_mapping:
            self._default_pool = value
        else:
            logger.error('{0} is not a valid pool type'.format(value))

    def define_dependency_node(self, target, dependency):
        self.target = target
        self.dependency = dependency

    def reset(self):
        self.randomize = False
        self.queue = []
        self.results = []

    @property
    def pool(self):
        return self.worker_pool

    @pool.setter
    def pool(self, value=None):
        if value == self.worker_pool:
            pass
        elif isinstance(value, self.pool_types):
            self.worker_pool = value
        elif value in self.pool_mapping:
            self.default_pool = value
        elif value in self.pool_types:
            self.worker_pool = value(self.pool_size)

    def create_pool(self, pool=None):
        if isinstance(pool, self.pool_types):
            self.pool = pool
            return
        elif self.has_active_pool():
            logger.debug('pool exists, not creating a new pool')
            return
        elif pool in self.pool_mapping:
            self.default_pool = pool
        elif self.default_pool == 'lazy' or pool == 'lazy':
            logger.debug('avoiding creating a lazy pool')
            return
        elif pool is None:
            pool = self.default_pool
        elif pool not in self.pool_mapping:
            m = '{0} is not a valid pool type, using the default: {1}'
            logger.error(m.format(pool, self.default_pool))
            pool = self.default_pool

        if self.root_app is False:
            logger.warning('creating a worker pool on a sub_app is probably an error.')

        self.pool = self.pool_mapping[pool](self.pool_size)

    def has_active_pool(self):
        if isinstance(self.worker_pool, self.pool_types):
            return True
        else:
            return False

    @property
    def queue_has_apps(self):
        for task in self.queue:
            if isinstance(task, BuildApp):
                return True

        return False

    def clean_queue(self):
        old_queue_len = len(self.queue)

        new_queue = []
        for task in self.queue:
            if isinstance(task, BuildApp):
                if len(task.queue) == 0:
                    logger.warning('dropping an empty app from task queue')
                    continue
                else:
                    if task.pool is None:
                        task.pool = self.pool
                    new_queue.append(task)
            elif isinstance(task, Task):
                new_queue.append(task)

        self.queue = new_queue

        if len(self.queue) < old_queue_len:
            logger.warning('cleansed queue of empty apps')

    def close_pool(self):
        if self.has_active_pool():
            self.worker_pool.close()
            self.worker_pool = None

    def sub_app(self):
        app = BuildApp()
        app.force = self.force
        app.root_app = False
        app.default_pool = self.default_pool
        app.pool = self.pool

        if self.conf is not None:
            app.conf = self.conf

        return app

    def extend_queue(self, tasks):
        if isinstance(tasks, (Task, BuildApp)):
            self.add(tasks)
        elif tasks is None or len(tasks) == 0:
            return
        else:
            for task in tasks:
                if isinstance(task, collections.Iterable):
                    if len(task) == 0:
                        continue
                    else:
                        app = self.sub_app()
                        app.extend_queue(task)
                        self.add(app)
                else:
                    self.add(task)

    def add(self, task=None, conf=None):
        """
        Adds a new :class:`~giza.app.BuildApp()` or :class:`~giza.task.Task()`
        to the :class:`~giza.app.BuildApp()` object.

        :param string,Task,BuildApp task: Optional. If not specified,
           :meth:`~giza.app.BuildApp.add()` creates and returns a new
           :class:`~giza.task.Task()` object. You can pass the string ``task``
           or the class :class:`~giza.task.Task` to explicitly create a new
           Task, or pass an existing :class:`~giza.task.Task()` instance to add
           that task to the :class:`~giza.app.BuildApp()` instance. You can
           also pass the string ``app`` or the :class:`~giza.app.BuildApp`
           class, to create and add new :class:`~giza.app.BuildApp()`: pass an
           existing :class:`~giza.app.BuildApp()` instance to add that that
           operation grouping to the queue.

        :returns: A reference to a :class:`~giza.app.BuildApp()` or
           :class:`~giza.task.Task()` object in the :class:`~giza.app.BuildApp()`

        :raises: :exc:`TypeError` if the ``task`` argument is invalid.

        """
        if conf is not None:
            self.conf = conf

        if task is None or task in (Task, 'task'):
            t = Task()
            t.conf = self.conf
            t.force = self.force
            self.queue.append(t)
            return t
        elif task in (MapTask, 'map'):
            t = MapTask()
            t.conf = self.conf
            t.force = self.force
            self.queue.append(t)
            return t
        elif task in (BuildApp, 'app'):
            t = self.sub_app()
            self.queue.append(t)
            return t
        else:
            if isinstance(task, Task):
                task.force = self.force
                if task.conf is None:
                    task.conf = self.conf

                self.queue.append(task)
                return task
            elif isinstance(task, BuildApp):
                task.root_app = False
                task.defualt_pool = self.default_pool
                task.force = self.force
                task.pool = self.pool
                self.queue.append(task)
                return task
            else:
                raise TypeError('invalid task type')

    def _run_mixed_queue(self):
        group = []

        for task in self.queue:
            if isinstance(task, Task):
                group.append(task)
            elif isinstance(task, BuildApp):
                if len(group) >= 1:
                    if self.randomize is True:
                        random.shuffle(group)

                    self.results.extend(self.pool.runner(group))
                    group = []

                if task.pool is None:
                    task.pool = self.pool

                self.results.extend(task.run())

        if len(group) != 0:
            self.results.extend(self.pool.runner(group))

    def run(self, randomize=None):
        "Executes all tasks in the :attr:`~giza.app.BuildApp.queue`."

        self.randomize = randomize
        self.create_pool()

        # remove empty apps from queue
        self.clean_queue()

        if len(self.queue) == 0:
            pass  # we could warn here, and while it's not ideal, its mostly harmless.
        elif self.queue_has_apps is True:
            self._run_mixed_queue()
        else:
            if self.randomize is True:
                random.shuffle(self.queue)

            self.results.extend(self.pool.runner(self.queue))

        self.queue = []
        return self.results

    @contextlib.contextmanager
    def context(self, conf=None, randomize=None):
        if len(self.queue) == 0:
            yield self
            self.run(randomize)
        else:
            app = self.add('app')
            yield app
            app.run(randomize)
