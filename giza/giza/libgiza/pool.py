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
:mod:`~giza.pool` provides methods for executing the tasks in a
:class:`~giza.app`. The base class :class:`~giza.pool.WorkerPool` provides core
functionality, while additional sub-classes use different parallelism
mechanisms.
"""

import logging
import multiprocessing
import multiprocessing.dummy
import numbers
import sys

from libgiza.task import MapTask, Task

logger = logging.getLogger('giza.pool')


class PoolConfigurationError(Exception):
    pass


class PoolResultsError(Exception):
    pass


def run_task(task):
    "helper to call run method on task so entire operation can be pickled for process pool support"

    try:
        result = task.run()
    except KeyboardInterrupt:
        logger.error('task received interrupt.')

    return result


class WorkerPool(object):
    @property
    def pool_size(self):
        try:
            return self._pool_size
        except:
            return 2

    @pool_size.setter
    def pool_size(self, value):
        if isinstance(value, numbers.Number):
            self._pool_size = value
        else:
            self._pool_size = multiprocessing.cpu_count()
            logger.error('{0} is not a valid pool size, using number of cores'.format(str(value)))

    def __enter__(self):
        return self.p

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.p.close()
        self.p.join()

    def runner(self, jobs):
        return self.get_results(self.async_runner(jobs))

    def async_runner(self, jobs):
        results = []

        for job in jobs:
            if not hasattr(job, 'run'):
                raise TypeError('task "{0}" is not a valid Task'.format(job))

            if job.needs_rebuild is True:
                self.add_task(job, results)
            else:
                logger.debug("{0} does not need a rebuild".format(job.target))

        return results

    def do_finalizers(self, job, results):
        final = None

        if len(job.finalizers) == 0:
            pass
        else:
            for task in job.finalizers:
                if isinstance(task, tuple) and task[0] in ('final', 'last'):
                    if final is not None:
                        logger.error('can only define one final finalizer task')
                    else:
                        final = task[1]
                else:
                    if task.needs_rebuild is True:
                        self.add_task(task, results)

        self.add_task(final, results)

    def add_task(self, job, results):
        idx = len(results) + 1

        if job is None:
            return
        elif hasattr(job, 'queue'):
            m = 'cannot use finalizers that have queues. skipping tasks ({0})'
            logger.warning(m.format(len(job.queue)))

        if isinstance(job, MapTask):
            results.append((job, idx, self.p.map_async(job.job, job.iter)))
        else:
            results.append((job, idx, self.p.apply_async(run_task, args=[job])))

    def get_results(self, results):
        has_errors = False

        retval = []
        errors = []

        has_finalizers = False
        for job, _, __ in results:
            if len(job.finalizers) >= 1:
                has_finalizers = True
                break

        # the while loop is required so that finalizer tasks begin running as
        # soon as their parent completes, but is otherwise functionally
        # equivalent . However, the while loop spins the main thread, which is
        # *much* slower with thread/gevent pools
        if has_finalizers is True:
            while True:
                for job, idx, ret in results:
                    if ret.ready():
                        try:
                            task_result = ret.get()
                        except Exception as e:
                            if job.ignore_errors is True:
                                m = 'caught error "{0}", waiting for other tasks to finish'
                                logger.error(m.format(e))
                                has_errors = True
                                errors.append((job, e))
                            else:
                                m = "caught error {0} with task {1}. exiting now."
                                logger.error(m.format(e, job.description))
                                raise SystemExit(1)

                        retval.append((idx, task_result))
                        self.do_finalizers(job, results)
                        results.remove((job, idx, ret))

                if len(results) == 0:
                    break

            retval.sort(key=lambda x: x[0])
        else:
            for job, idx, ret in results:
                try:
                    retval.append((idx, ret.get()))
                except Exception as e:
                    if job.ignore_errors is True:
                        m = 'caught error "{0}" in {1}, waiting for other tasks to finish'
                        logger.error(m.format(e, job.description))
                        has_errors = True
                        errors.append((job, e))
                    else:
                        m = "caught error {0} with task {1}. exiting now."
                        logger.error(m.format(e, job.description))
                        raise SystemExit(1)

        if has_errors is True:
            error_list = []
            for job, err in errors:
                error_list.append(err)

            logger.error(PoolResultsError(error_list))
            raise SystemExit(1)
        else:
            return [r[1] for r in retval]


class SerialPool(object):
    def __init__(self, pool_size=0):
        self.p = None
        self.pool_size = pool_size
        logger.debug('new phony "serial" pool object')

    def close(self):
        pass

    def get_results(self, results):
        return results

    def runner(self, jobs):
        results = []
        for job in jobs:
            if job.needs_rebuild is False:
                continue

            if job.description is not None:
                msg = job.description
            else:
                msg = str(job.job)

            logger.debug('running: ' + msg)
            results.append(job.run())

            if isinstance(job, Task) and len(job.finalizers) >= 1:
                logger.debug('finalizing: ' + msg)
                results.extend(job.finalize())

        return results

    async_runner = runner


class ThreadPool(WorkerPool):
    def __init__(self, pool_size=None):
        self.pool_size = pool_size
        self.p = multiprocessing.dummy.Pool(self.pool_size)
        logger.info('new thread pool object')


class ProcessPool(WorkerPool):
    def __init__(self, pool_size=None):
        self.pool_size = pool_size
        self.p = multiprocessing.Pool(self.pool_size)
        logger.info('new process pool object')


class EventPool(WorkerPool):
    def __init__(self, pool_size=None):
        self.pool_size = pool_size

        if sys.version_info >= (3, 0):
            logger.error('gevent is not supported on this platform, using threads')
            self.p = multiprocessing.dummy.Pool(self.pool_size)
        else:
            try:
                import gevent.pool
                self.p = gevent.pool.Pool(self.pool_size)
                logger.info('new event pool object')
            except ImportError:
                logger.error('gevent is not supported on this system, using threads')
                self.p = multiprocessing.dummy.Pool(self.pool_size)
