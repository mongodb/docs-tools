import logging
import os.path
import collections

logger = logging.getLogger('giza.task')

from giza.config.main import Configuration
from giza.files import md5_file

class MapTask(Task):
    def __init__(self, job=None, description=None, target=None, dependency=None):
        super(Task, self).__init__(job=job, description=description,
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
        if isinstance(value, collections.Callable):
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

############### Dependency Checking ###############

def check_dependency(target, dependency):
    if dependency is None:
        return True

    if isinstance(target, list):
        if len(target) == 1:
            target = target[0]
        else:
            return check_multi_dependency(target, dependency)

    if os.path.exists(target) is False:
        return True


    def needs_rebuild(targ_t, dep_f):
        if targ_t < os.path.getmtime(dep_f):
            return True
        else:
            return False

    target_time = os.path.getmtime(target)
    if isinstance(dependency, list):
        for dep in dependency:
            if needs_rebuild(target_time, dep) is True:
                return True
        return False
    else:
        return needs_rebuild(target_time, dependency)

def check_multi_dependency(target, dependency):
    for idx, t in enumerate(target):
        if check_dependency(t, dependency) is True:
            return True

    return False

############### Hashed Dependency Checking ###############

def check_hashed_dependency(target, dependency, dep_map, conf):
    def normalize_fn(fn):
        if not fn.startswith(conf.paths.projectroot):
            if fn.startswith(conf.paths.source):
                fn = os.path.join(conf.paths.projectroot, fn)
            if fn.startswith('/'):
                fn = os.path.join(conf.paths.projectroot,
                                  conf.paths.source,
                                  fn[1:])

        return fn

    def needs_rebuild(t, d):
        if dep_map is None:
            return check_dependency(t, d)
        elif d in dep_map:
            fn_hash = md5_file(d)
        else:
            return check_dependency(t, d)

        if dep_map[d] == fn_hash:
            return False
        else:
            return True

    if target is None or dependency is None:
        return True

    if isinstance(target, list):
        target = [ normalize_fn(t) for t in target ]
        for f in target:
            if not os.path.exists(f):
                return True
    else:
        target = normalize_fn(target)
        if not os.path.exists(target):
            return True

    if isinstance(dependency, list):
        dependency = [ normalize_fn(d) for d in dependency ]
        for dep in dependency:
            if needs_rebuild(target, dep) is True:
                return True
        return False
    else:
        dependency = normalize_fn(dependency)
        return needs_rebuild(target, dependency)
