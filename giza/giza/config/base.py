import logging
import os.path

logger = logging.getLogger('giza.config.base')

from giza.serialization import ingest_yaml_doc

class ConfigurationBase(object):
    def __init__(self, input_obj=None):
        self._state = {}
        self.ingest(input_obj)

    def ingest(self, input_obj=None):
        if input_obj is None:
            return
        elif isinstance(input_obj, dict):
            pass
        elif os.path.exists(input_obj):
            input_obj = ingest_yaml_doc(input_obj)
        else:
            msg = 'cannot ingest Configuration obj from object with type {0}'.format(type(input_obj))
            logger.critical(msg)
            raise TypeError(msg)

        for key, value in input_obj.items():
            setattr(self, key, value)
            logger.debug('setting {0} using default setter in {1} object'.format(key, type(self)))

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        logger.warning('cannot set state record directly')

    def __contains__(self, key):
        return key in self.state

    def __setattr__(self, key, value):
        if key.startswith('_') or key in dir(self):
            object.__setattr__(self, key, value)
        else:
            msg = 'configuration object {0} lacks support for "{1}" value'.format(type(self), key)
            logger.error(msg)
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
            if k.startswith('_'):
                continue
            elif isinstance(v, ConfigurationBase):
                d[k] = v.dict()
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], ConfigurationBase):
                d[k] = [i.dict() for i in v ]
            elif self._is_value_type(v):
                d[k] = v
        return d

class RecursiveConfigurationBase(ConfigurationBase):
    def __init__(self, obj, conf):
        super(RecursiveConfigurationBase, self).__init__(obj)
        self._conf = None
        self.conf = conf

    @property
    def conf(self):
        return self._conf

    @conf.setter
    def conf(self, value):
        if isinstance(value, ConfigurationBase):
            self._conf = value
        else:
            m = 'invalid configuration object: {0}'.format(value)
            logger.error(m)
            raise TypeError(m)
