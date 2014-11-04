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
:mod:`task` stores the :class:`~giza.task.Task()` and
:class:`~giza.task.MapTask()` classes which represent single units of work in
the context of a :class:`~giza.app.BuildApp()` procedure.

:mod:`task` also has a number of dependency resolution helper functions.
"""

import logging
import sys
import os.path
import collections

logger = logging.getLogger('giza.task')

from giza.config.main import ConfigurationBase
from giza.tools.files import md5_file

if sys.version_info >= (3, 0):
    basestring = str

class Task(object):
    """
    Provides a common interface for defining an operational unit of work in a
    concurrent :class:`~giza.app.BuildApp()` environment.

    With :attr:`~giza.task.Task.target` and :attr:`~giza.task.Task.dependency`
    defined, if a ``target`` file exists and was modified after the
    ``dependency`` file, the :class:`~giza.task.Task()` operation becomes a
    no-op, unless forced.
    """

    def __init__(self, job=None, description=None, target=None, dependency=None):
        """
        All arguments are optional. You can define a :class:`~giza.task.Task()`
        either upon creation, or after creation by modifying attributes.

        :param callable job: A callable object that the task will execute.

        :param string description: Describes the task. Used in error messages.

        :param string target: A file name. A path to a file that the task will create.

        :param string dependency: A file name. A path to a file that the task
           depends on. When specified, the task will only run if forced or if
           the ``depdendency`` file is newer than the target file.
        """

        self.spec = {}
        self._conf = None
        self._args = None
        if job is not None:
            self.job = job
        self.args_type = None
        self.description = description

        self.target = target
        self.dependency = dependency

        logger.debug('created task object calling {0}, for {1}'.format(job, description))
        self._task_id = None

    @property
    def task_id(self):
        if self._task_id is None:
            self._task_id = hash(str(self.job)) + hash(str(self.args))

        return self._task_id

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

    def define_dependency_node(self, target, dependency):
        self.target = target
        self.dependency = dependency

    @property
    def conf(self):
        return self._conf

    @conf.setter
    def conf(self, value):
        if isinstance(value, ConfigurationBase):
            self._conf = value
        else:
            raise TypeError

    @property
    def job(self):
        return self.spec['job']

    @job.setter
    def job(self, value):
        if isinstance(value, collections.Callable):
            self.spec['job'] = value
        else:
            raise TypeError

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, value):
        if isinstance(value, dict):
            self.args_type = 'kwargs'
            self._args = value
        elif isinstance(value, (list, tuple)):
            self.args_type = 'args'
            self._args = value
        elif isinstance(value, basestring):
            self.args_type = 'args'
            self._args = [value]
        else:
            logger.critical(type(value))

    @property
    def needs_rebuild(self):
        if self.target is None:
            logger.warning('no target specified for: ' + str(self.job))
            return True
        elif self.dependency is None or self.conf.runstate.force is True:
            return True
        else:
            return check_dependency(self.target, self.dependency)

    def run(self):
        logger.debug('({0}) calling {1}'.format(self.task_id, self.job))
        if self.args_type == 'kwargs':
            r = self.job(**self.args)
        elif self.args_type == 'args':
            r = self.job(*self.args)
        else:
            r = self.job()

        logger.debug('completed running task {0}, {1}'.format(self.task_id, self.description))
        return r

############### Dependency Checking ###############

def check_dependency(target, dependency):
    """
    Determines if a target requires rebuilding based on a provided
    dependency.

    :param string target: A file name.

    :param dependency: A file name or list of file names.
    :type dependency: string, list

    :returns: A boolean. If either the ``target`` or ``dependency`` doesn't
       exist, or if the ``target`` was modified more recently than the
       ``dependency`` returns ``True`` otherwise returns ``False``.

    :func:`~giza.task.check_dependency()` Accepts dependencies in the form of a
    single file name, or as a list, and will return ``True`` if *any* dependent
    file is newer than the target. Also returns ``True`` when:

    - ``target`` or ``dependency`` is ``None``.

    - ``target`` or ``dependency`` does not exist.
    """

    if dependency is None:
        return True
    elif target is None:
        return True
    elif isinstance(target, list):
        for t in target:
            if os.path.exists(t) is False:
                return True
            else:
                return check_dependency(t, dependency)
    elif os.path.exists(target) is False:
        return True
    elif isinstance(dependency, list):
        target_time = os.path.getmtime(target)
        for dep in dependency:
            if dep is None:
                return True
            elif target_time < os.path.getmtime(dep):
                return True
        return False
    elif os.path.exists(dependency):
        if os.path.getmtime(target) < os.path.getmtime(dependency):
            return True
        else:
            return False
    else:
        logger.error('{0} is not a valid dependency'.format(dependency))
        return True

class MapTask(Task):
    """
    A variant of :class:`~giza.task.Task()` that defines a task that like the
    kind of operation that would run in a :func:`map()` function, processing the
    contents of an operable with a single function.
    """

    def __init__(self, job=None, description=None, target=None, dependency=None):
        super(MapTask, self).__init__(job=job, description=description,
                                   target=target, dependency=dependency)
        self._iter = []

    @property
    def iter(self):
        return self._iter

    @iter.setter
    def iter(self, value):
        if isinstance(value, collections.Iterable):
            self._iter = value
        else:
            raise TypeError

    def run(self):
        return map(self.job, self.iter)

############### Hashed Dependency Checking ###############

def normalize_dep_path(fn, conf, branch):
    fn = fn.rstrip()
    if not fn.startswith(conf.paths.projectroot):
        if fn.startswith(conf.paths.branch_source) or fn.startswith(conf.paths.source):
            fn = os.path.join(conf.paths.projectroot, fn)
        elif fn.startswith('/'):
            if branch is False:
                fn = os.path.join(conf.paths.projectroot,
                                  conf.paths.source,
                                  fn[1:])
            else:
                fn = os.path.join(conf.paths.projectroot,
                                  conf.paths.branch_source,
                                  fn[1:])

    return fn

def check_hashed_dependency(fn, dep_map, conf):
    """
    :return: True when any of the files have changed.
    """
    # logger.info('checking dependency for: ' + fn)

    fn = normalize_dep_path(fn, conf, branch=False)

    if dep_map is None:
        return True
    elif not os.path.exists(fn):
        return True
    elif fn in dep_map:
        if dep_map[fn] != md5_file(fn):
            return True
        else:
            return False
    else:
        return False
