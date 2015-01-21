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

from contextlib import contextmanager

logger = logging.getLogger('giza.config.base')

from giza.tools.serialization import ingest_yaml_doc, ingest_json_doc, write_json, write_yaml

class ConfigurationError(Exception):
    pass

class ConfigurationBase(object):
    _option_registry = []
    _version = 0

    def __init__(self, input_obj=None):
        self._source_fn = None
        self._state = {}
        self.ingest(input_obj)

    def ingest(self, input_obj):
        if input_obj is None:
            return

        input_obj = self._prep_load_data(input_obj)

        for key, value in input_obj.items():
            setattr(self, key, value)

    def _prep_load_data(self, input_obj):
        if isinstance(input_obj, dict):
            pass
        elif not isinstance(input_obj, ConfigurationBase) and os.path.isfile(input_obj):
            self._source_fn = input_obj

            if input_obj.endswith('json'):
                input_obj = ingest_json_doc(input_obj)
            elif input_obj.endswith('yaml'):
                input_obj = ingest_yaml_doc(input_obj)
            else:
                logger.error("file {0} has unknown data format".format(input_obj))
        else:
            msg = 'cannot ingest Configuration obj from object with type {0}'.format(type(input_obj))
            logger.critical(msg)
            raise TypeError(msg)

        return input_obj

    def __getattr__(self, key):
        try:
            return object.__getattribute__(self, key)
        except AttributeError as e:
            if key in self._option_registry:
                return self.state[key]
            else:
                m = 'key "{0}" in configuration object ({1}) does not exist'.format(key, type(self))
                if not key.startswith('_'):
                    logger.debug(m)
                raise AttributeError(m, e.message)

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

    def dict(self, safe=True):
        d = {}

        def get_dict_value(v):
            if isinstance(v, ConfigurationBase):
                return v.dict(safe)
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], ConfigurationBase):
                return [i.dict() for i in v ]
            elif isinstance(v, dict):
                sub_d = {}
                for key,value, in v.items():
                    sub_d[key] = get_dict_value(value)
                return sub_d
            elif self._is_value_type(v):
                return v
            else:
                return 'error'

        for key, value in self.state.items():
            if safe in (True, None):
                if key.startswith('_'):
                    continue
                elif key in ('pass', 'password', 'token'):
                    d[key] = 'redacted'
                else:
                    d[key] = get_dict_value(value)
            elif safe is False:
                d[key] = get_dict_value(value)

        return d

    def write(self, fn=None):
        if fn is None:
            if self._source_fn is None:
                logger.error('cannot write object to unspecified file.')
                return
            else:
                fn = self._source_fn

        if 'v' not in self.state:
            self.state['v'] = self._version

        if fn.endswith('json'):
            write_json(self.dict(safe=False), fn)
        elif fn.endswith('yaml'):
            write_yaml(self.dict(safe=False), fn)

    @classmethod
    @contextmanager
    def persisting(cls, fn, override=False):
        if not os.path.isfile(fn):
            write_json({}, fn)

        if override is False:
            data = cls(fn)
        elif override is True:
            data = cls()
            input_data = data._prep_load_data(fn)
            data.state.update(input_data)

        yield data

        data.write(fn)

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
