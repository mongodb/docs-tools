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

import logging
import os.path

logger = logging.getLogger('giza.config.base')

from giza.serialization import ingest_yaml_doc

class ConfigurationBase(object):
    _option_registry = []

    def __init__(self, input_obj=None):
        self._state = {}
        self.ingest(input_obj)

    def ingest(self, input_obj=None):
        if input_obj is None:
            return
        elif isinstance(input_obj, dict):
            pass
        elif not isinstance(input_obj, ConfigurationBase) and os.path.exists(input_obj):
            input_obj = ingest_yaml_doc(input_obj)
        else:
            print(input_obj)
            msg = 'cannot ingest Configuration obj from object with type {0}'.format(type(input_obj))
            logger.critical(msg)
            raise TypeError(msg)

        for key, value in input_obj.items():
            setattr(self, key, value)
            logger.debug('setting {0} using default setter in {1} object'.format(key, type(self)))

    def __getattr__(self, key):
        try:
            return object.__getattribute__(self, key)
        except AttributeError as e:
            if key in self._option_registry:
                return self.state[key]
            else:
                m = 'key "{0}" in configuration object does not exist'.format(key)
                logger.debug(m)
                raise AttributeError(m)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        logger.warning('cannot set state record directly')

    def __contains__(self, key):
        return key in self.state

    def __setattr__(self, key, value):
        if key in self._option_registry:
            self.state[key] = value
        elif key.startswith('_') or key in dir(self):
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
        return str(self.dict())

    def dict(self):
        d = {}
        for k,v in self.state.items():
            if k.startswith('_'):
                continue
            elif k in ('pass', 'password', 'token'):
                d[k] = 'redacted'
            elif isinstance(v, ConfigurationBase):
                d[k] = v.dict()
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], ConfigurationBase):
                d[k] = [i.dict() for i in v ]
            elif self._is_value_type(v):
                d[k] = v
        return d

class RecursiveConfigurationBase(ConfigurationBase):
    def __init__(self, obj, conf):
        self._conf = None
        self.conf = conf
        super(RecursiveConfigurationBase, self).__init__(obj)

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
