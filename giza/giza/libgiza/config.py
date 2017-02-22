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
import json
import contextlib
import sys
import numbers

import yaml

logger = logging.getLogger('giza.libgiza.config')

if sys.version_info >= (3, 0):
    basestring = str


class ConfigurationError(Exception):
    pass


class OutputError(Exception):
    pass


class ConfigurationBase(object):
    _option_registry = []
    _redacted_keys = ['pass', 'password', 'token', 'key', 'secret']
    _version = 0

    def __init__(self, input_obj=None):
        self._source_fn = None
        self._state = {}
        self.ingest(input_obj)

    def ingest(self, input_obj):
        if input_obj is None:
            return

        input_obj = self._prep_load_data(input_obj)

        # We need deterministic iteration order---"paths" must come before
        # "git", or else we have an uninitialized read from Configuration.paths
        items = list(input_obj.items())
        items.sort(reverse=True)

        for key, value in items:
            try:
                setattr(self, key, value)
            except AttributeError as e:
                m = '{0}({1}) ingestion error with {2} key and {3} value, for {4} obj'
                m = m.format(e, type(e), key, value, type(self))
                logger.error(m)
                raise ConfigurationError(m)

    def _prep_load_data(self, input_obj):
        if isinstance(input_obj, dict):
            return input_obj
        elif not isinstance(input_obj, ConfigurationBase) and os.path.isfile(input_obj):
            self._source_fn = input_obj

            with open(input_obj, 'r') as f:
                if input_obj.endswith('json'):
                    input_obj = json.load(f)
                elif input_obj.endswith('yaml') or input_obj.endswith('yml'):
                    input_obj = yaml.safe_load(f)
                else:
                    logger.error("file {0} has unknown data format".format(input_obj))

            if input_obj is None:
                input_obj = {}
        else:
            msg = 'cannot ingest Configuration obj from {0} object'.format(type(input_obj))
            logger.critical(msg)
            raise TypeError(msg)

        return input_obj

    def __contains__(self, key):
        if key in self.state:
            return True
        elif key.startswith("_") and hasattr(self, key):
            return True
        else:
            return False

    def __getattr__(self, key):
        try:
            return object.__getattribute__(self, key)
        except AttributeError as e:
            m = 'key "{0}" in configuration object ({1}) is not defined'.format(key, type(self))
            if key in self._option_registry:
                try:
                    return self.state[key]
                except KeyError:
                    raise AttributeError(m, str(e))
            else:
                if not key.startswith('_'):
                    logger.debug(m)
                raise AttributeError(m, str(e))

    def __setattr__(self, key, value):
        if key in self._option_registry:
            self.state[key] = value
        elif key.startswith('_') or key in dir(self):
            object.__setattr__(self, key, value)
        else:
            msg = 'configuration object {0} lacks support for "{1}" value'.format(type(self), key)
            logger.error(msg)
            raise TypeError(msg)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        logger.warning('cannot set state record directly')

    @staticmethod
    def _is_value_type(value):
        acceptable_types = (ConfigurationBase, basestring, list, numbers.Number)

        if isinstance(value, acceptable_types):
            return True
        else:
            return False

    def __repr__(self):
        return str(self.dict())

    def __get_dict_value__(self, v, safe=True):
        if isinstance(v, ConfigurationBase):
            return v.dict(safe)
        elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], ConfigurationBase):
            return [i.dict() for i in v]
        elif isinstance(v, dict):
            sub_d = {}
            for key, value, in v.items():
                sub_d[key] = self.__get_dict_value__(value)
            return sub_d
        elif self._is_value_type(v):
            return v
        else:
            return 'error'

    def dict(self, safe=True):
        d = {}

        for key, value in self.state.items():
            if safe in (True, None):
                if key != "_id" and key.startswith('_'):
                    continue
                elif key in self._redacted_keys:
                    d[key] = 'redacted'
                else:
                    d[key] = self.__get_dict_value__(value, safe)
            elif safe is False:
                d[key] = self.__get_dict_value__(value, safe)

        return d

    def write(self, fn=None, add_version=False):
        if fn is None:
            if self._source_fn is None:
                logger.error('cannot write object to unspecified file.')
                return
            else:
                fn = self._source_fn

        if not isinstance(fn, basestring):
            raise OutputError("unsupported file format: {0}".format(fn))

        if add_version is True and 'v' not in self.state:
            self.state['v'] = self._version

        if fn.endswith('json'):
            with open(fn, 'w') as f:
                json.dump(self.dict(safe=False), f, indent=3, sort_keys=True)
        elif fn.endswith('yaml') or fn.endswith('yml'):
            with open(fn, 'w') as f:
                yaml.safe_dump(self.dict(safe=False), f, default_flow_style=False)
        else:
            raise OutputError("unsupported file format: {0}".format(fn))

    @classmethod
    @contextlib.contextmanager
    def persisting(cls, fn, override=False):
        if not os.path.isfile(fn):
            with open(fn, 'w') as f:
                json.dump({}, f, indent=3)

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
