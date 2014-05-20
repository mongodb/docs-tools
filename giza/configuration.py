import logging
import os.path

logger = logging.getLogger(os.path.basename(__file__))

from utils.structures import BuildConfiguration
from utils.serialization import ingest_yaml_doc

class ConfigurationBase(object):
    def __init__(self, input_obj=None):
        self._state = {}

        if input_obj is None:
            return

        if isinstance(input_obj, dict):
            pass
        elif os.path.exists(input_obj):
            input_obj = ingest_yaml_doc(input_obj)
        else:
            msg = 'cannot instantiate Configuration obj with type {0}'.format(type(input_obj))
            logger.critical(msg)
            raise TypeError(msg)

        for k, v in input_obj.items():
            if '-' in k:
                k = k.replace('-', '_')

            if k in dir(self):
                logger.debug('setting {0} with a setter'.format(k))
                object.__setattr__(self, k, v)
            elif isinstance(v, dict):
                logger.warning('conf object lacks "{0}" attr (dict value)'.format(k))
                v = ConfigurationBase(v)
                object.__setattr__(self, k, v)
                self._state[k] = v
            else:
                logger.warning('conf object lacks "{0}" attr'.format(k))
                self._state[k] = v

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        logger.warning('cannot set state record directly')

    def __getattr__(self, key):
        return self.state[key]

    def __contains__(self, key):
        return key in self.state

    def __setattr__(self, key, value):
        if key.startswith('_') or key in dir(self):
            object.__setattr__(self, key, value)
        elif self._is_value_type(value):
            self.state[key] = value
        else:
            msg = 'configuration object lacks support for {0} value'.format(key)
            logger.critical(msg)
            raise TypeError(msg)

    @staticmethod
    def _is_value_type(value):
        acceptable_types = (ConfigurationBase, basestring, list, int, long,
                            float, complex)

        if isinstance(value, acceptable_types):
            return True
        else:
            return False

    def __repr__(self):
        return str(self.state)

    def dict(self):
        d = {}
        for k,v in self.state.items():
            if isinstance(v, ConfigurationBase):
                d[k] = v.dict()
            else:
                d[k] = v
        return d

class ProjectConfig(ConfigurationBase):
    @property
    def name(self):
        return self.state['name']

    @name.setter
    def name(self, value):
        self.state['name'] = value

    @property
    def tag(self):
        return self.state['tag']

    @tag.setter
    def tag(self, value):
        self.state['tag'] = value

    @property
    def url(self):
        return self.state['url']

    @url.setter
    def url(self, value):
        self.state['url'] = value

    @property
    def title(self):
        return self.state['title']

    @url.setter
    def title(self, value):
        self.state['title'] = value

from utils.git import GitRepo

class GitConfigBase(ConfigurationBase):
    def __init__(self, obj, repo=None):
        super(GitConfigBase, self).__init__(obj)
        self._repo = repo

    @property
    def repo(self):
        return self._repo

    @repo.setter
    def repo(self, path=None):
        self._repo = GitRepo(path)

class GitConfig(GitConfigBase):
    @property
    def commit(self):
        c = self.repo.sha('HEAD')
        self.state['commit'] = c
        return c

    @property
    def branches(self):
        if 'branches' not in self.state:
            self.branches = GitBranchConfig(None, self.repo)
        return self.state['branches']

    @branches.setter
    def branches(self, value):
        self.state['branches'] = GitBranchConfig(obj={}, repo=self.repo)

class GitBranchConfig(GitConfigBase):
    @property
    def current(self):
        b = self.repo.current_branch()
        self.state['current'] = b
        return b

class PathsConfig(ConfigurationBase):
    @property
    def projectroot(self):
        p = os.getcwd()
        self.state['projectroot'] = os.getcwd()
        return p

class Configuration(ConfigurationBase):
    @property
    def project(self):
        return self.state['project']

    @project.setter
    def project(self, value):
        self.state['project'] = ProjectConfig(value)

    @property
    def paths(self):
        return self.state['paths']

    @paths.setter
    def paths(self, value):
        self.state['paths'] = PathsConfig(value)

    @property
    def git(self):
        return self.state['git']

    @git.setter
    def git(self, value):
        c = GitConfig(value)
        c.repo = self.paths.projectroot
        self.state['git'] = c
