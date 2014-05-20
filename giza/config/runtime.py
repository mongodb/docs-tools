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
