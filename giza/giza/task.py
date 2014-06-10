import logging
import os.path
import collections

logger = logging.getLogger(os.path.basename(__file__))

from giza.config.main import Configuration
from giza.tools.jobs.dependency import check_dependency

class Task(object):
    def __init__(self):
        self.spec = {}
        self._conf = None
        self._args = None
        self.default_pool = 'process'
        self.job = None
        self.args_type = None
        self.description = None
        self.target = None
        self.dependency = None

    @property
    def conf(self):
        return self._conf

    @conf.setter
    def conf(self, value):
        if isinstance(value, Configuration):
            self._conf = value

    @property
    def job(self):
        return self.spec['job']

    @job.setter
    def job(self, value):
        if isinstance(value, collections.Callable) or value is None:
            self.spec['job'] = value
        else:
            logger.error('{0} is not callable'.format(self.spec['job']))
            raise TypeError

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, value):
        if isinstance(value, dict):
            self.args_type = 'kwargs'
            self._args = value
        elif isinstance(value, list):
            self.args_type = 'args'
            self._args = value
        elif isinstance(value, basestring):
            self.args_type = 'args'
            self._args = [value]
        else:
            logger.critical("task doesn't support args of type {0}".format(type(value)))

    @property
    def needs_rebuild(self):
        if (self.target is None or self.dependency is None or self.conf.runstate.force is True):
            return True
        else:
            return check_dependency(self.target, self.dependency)

    def run(self):
        task_id = hash(str(self.job)) + hash(str(self.args))
        logger.debug('({0}) calling {1} with args {2}'.format(task_id, self.job, self.args))
        if self.args_type == 'kwargs':
            self.job(**self.args)
        elif self.args_type == 'args':
            self.job(*self.args)
        else:
            self.job()
        logger.debug('(completed running task {0}'.format(task_id))
