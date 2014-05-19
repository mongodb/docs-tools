import logging
import os.path

logger = logging.getLogger(os.path.basename(__file__))

from utils.structures import BuildConfiguration

class ConfigurationBase(object):
    def __init__(self, fn=None):
        self._state = {}

        if fn is not None and os.path.exists(fn):
            conf = BuildConfiguration(fn)
            for k in conf:
                self._state[k] = conf[k]

    def __getitem__(self, key):
        return self._state[key]

    def __contains__(self, key):
        return key in self._state

    def __setattr__(self, key, value):
        if key.startswith('_') or hasattr(self, key):
            object.__setattr__(self, key, value)
        else:
            self._state[key] = value

    __getattr__ = __getitem__

    def __repr__(self):
        return str(self._state)

    def dict(self):
        return self._state

class ExampleConfig(ConfigurationBase):
    @property
    def a(self):
        return self._state['a'] + 1

    @a.setter
    def a(self, key):
        if isinstance(key, list):
            print "refusing to add list"
        else:
            self._state['a'] = key

class Configuration(ConfigurationBase):
    pass
