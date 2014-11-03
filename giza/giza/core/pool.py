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

import multiprocessing
import multiprocessing.dummy
import logging
import random

logger = logging.getLogger('giza.pool')

from giza.core.task import MapTask
from giza.config.helper import new_skeleton_config

class PoolConfigurationError(Exception): pass
class PoolResultsError(Exception): pass

def run_task(task):
    "helper to call run method on task so entire operation can be pickled for process pool support"

    return task.run()


class WorkerPool(object):
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

        if len(jobs) == 1 and not isinstance(jobs[0], MapTask):
            j = jobs[0]
            results.append((j, j.run()))
        else:
            random.shuffle(jobs)
            for job in jobs:
                if not hasattr(job, 'run'):
                    raise TypeError('task "{0}" is not a valid Task'.format(job))

                if job.needs_rebuild is True:
                    if isinstance(job, MapTask):
                        results.append((job, self.p.map_async(job.job, job.iter)))
                    else:
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
        self.conf = new_skeleton_config(conf)
        logger.debug('new phony "serial" pool object')

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

            logger.info('running: ' + msg)
            results.append(job.run())

        return results

    async_runner = runner

class ThreadPool(WorkerPool):
    def __init__(self, conf=None):
        self.conf = new_skeleton_config(conf)
        self.p = multiprocessing.dummy.Pool(self.conf.runstate.pool_size)
        logger.info('new thread pool object')

class ProcessPool(WorkerPool):
    def __init__(self, conf=None):
        self.conf = new_skeleton_config(conf)
        self.p = multiprocessing.Pool(self.conf.runstate.pool_size)
        logger.info('new process pool object')

class EventPool(WorkerPool):
    def __init__(self, conf=None):
        self.conf = new_skeleton_config(conf)

        try:
            import gevent.pool
        except ImportError:
            raise PoolConfigurationError('gevent is not available')

        self.p = gevent.pool.Pool(self.conf.runstate.pool_size)
        logger.info('new event pool object')
