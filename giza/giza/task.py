import logging
import os.path

logger = logging.getLogger(os.path.basename(__file__))

from giza.tools.jobs.dependency import check_dependency
from giza.config.main import Configuration

class Task(object):
    def __init__(self, job=None, description=None, target=None, dependency=None):
        self.spec = {}
        self._conf = None
        self._args = None
        self.default_pool = 'process'
        self.job = job
        self.args_type = None
        self.description = description
        self.target = target
        self.dependency = dependency
        logger.debug('created task object calling {0}, for {1}'.format(job, description))

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
        #todo: assert value is callable
        if 1 == 1:
            self.spec['job'] = value

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
            logger.critical(type(value))

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
            r = self.job(**self.args)
        elif self.args_type == 'args':
            r = self.job(*self.args)
        else:
            r = self.job()

        logger.debug('completed running task {0}, {1}'.format(task_id, self.description))
        return r
