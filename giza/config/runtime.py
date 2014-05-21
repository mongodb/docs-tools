import logging
import os.path
import yaml

logger = logging.getLogger(os.path.basename(__file__))

from utils.shell import CommandError

from config.base import ConfigurationBase

class RuntimeStateConfig(ConfigurationBase):
    def __init__(self, obj=None):
        super(RuntimeStateConfig, self).__init__(obj)
        self._branch_conf = None
        self._conf = None

    @property
    def conf(self):
        return self._conf

    @conf.setter
    def conf(self, value):
        if isinstance(value, ConfigurationBase):
            self._conf = value
        else:
            m = 'invalid configuration object: {0}'.format(value)
            m.error(m)
            raise TypeError(m)

    @property
    def language(self):
        if 'language' not in self.state:
            return 'en'
        else:
            return self.state['language']

    @language.setter
    def language(self, value):
        self.state['language'] = value

    @property
    def edition(self):
        if 'edition' not in self.state:
            return False
        else:
            return self.state['edition']

    @edition.setter
    def edition(self, value):
        self.state['edition'] = value

    @property
    def branch_conf(self):
        if self._branch_conf is None:
            self.branch_conf = None

        return self._branch_conf

    @branch_conf.setter
    def branch_conf(self, value):
        fn = os.path.join(self.conf.paths.builddata, 'published_branches.yaml')

        if self.conf.git.branches.current == 'master'and not os.path.exists(fn):
            self._branch_conf = {}
        else:
            try:
                data = self.conf.git.repo.branch_file(path=fn, branch='master')
            except CommandError:
                logger.critical('giza not configured to work with buildbot repos')
                self._branch_conf = {}
                return

            self._branch_conf = yaml.load(data)

    @property
    def conf_path(self):
        return self.state['conf_path']

    @conf_path.setter
    def conf_path(self, value):
        self.state['conf_path'] = value

    @property
    def level(self):
        return self.state['level']

    @conf_path.setter
    def level(self, value):
        levels = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.critical
        }
        if value in levels:
            level = levels[value]
            logging.basicConfig(level=level)
            self.state['level'] = value

    @property
    def runner(self):
        if 'runner' not in self.state:
            self.runner = None

        return self.state['runner']

    @runner.setter
    def runner(self, value):
        supported_runners = ['process', 'thread', 'serial']

        if value is None:
            self.state['runner'] = 'process'
        elif value in supported_runners:
            self.state['runner'] = value
        else:
            m = '{0} is not a supported runner type, choose from: {1}'.format(vale, supported_runners)
            logger.error(m)
            raise TypeError(m)

    @property
    def force(self):
        if 'force' in self.state:
            return self.state['force']
        else:
            return False

    @force.setter
    def force(self, value):
        if isinstance(value, bool):
            self.state['force'] = value
        else:
            raise TypeError

    @property
    def function(self):
        return self.state['_entry_point']

    @function.setter
    def function(self, value):
        self.state['_entry_point'] = value
