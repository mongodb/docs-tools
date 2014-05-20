import logging
import os.path

logger = logging.getLogger(os.path.basename(__file__))

from utils.structures import BuildConfiguration
from utils.serialization import ingest_yaml_doc

class ConfigurationBase(object):
    def __init__(self, input_obj=None):
        self._state = {}

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
                object.__setattr__(self, k, v)
            elif isinstance(v, dict):
                logger.warning('conf object lacks "{0}" attr (dict value)'.format(k))
                v = ConfigurationBase(v)
                object.__setattr__(self, k, v)
                self.state[k] = v
            else:
                logger.warning('conf object lacks "{0}" attr'.format(k))
                self.state[k] = v

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
        if key.startswith('_') or hasattr(self, key):
            object.__setattr__(self, key, value)
        elif isinstance(value, ConfigurationBase):
            self.state[key] = value
        else:
            msg = 'configuration object lacks support for {0} value'.format(key)
            logger.critical(msg)
            raise TypeError(msg)

    def __repr__(self):
        return str(self.state)

    def dict(self):
        return self.state

class Configuration(ConfigurationBase):
    @property
    def project(self):
        return self.state['project']

    @project.setter
    def project(self, value):
        self.state['project'] = value

    @property
    def git(self):
        return self.state['git']

    @git.setter
    def git(self, value):
        self.state['git'] = value
