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

logger = logging.getLogger('giza.config.system')

from giza.config.base import RecursiveConfigurationBase, ConfigurationBase
from giza.serialization import ingest_yaml_list

class SystemConfig(RecursiveConfigurationBase):
    @property
    def make(self):
        return self.state['make']

    @make.setter
    def make(self, value):
        self.state['make'] = SystemMakeConfig(value)

    @property
    def tools(self):
        return self.state['tools']

    @tools.setter
    def tools(self, value):
        self.state['tools'] = SystemToolsConfig(value)

    @property
    def files(self):
        if 'files' not in self.state:
            self.files = []

        return self.state['files']

    @files.setter
    def files(self, value):
        if 'files' not in self.state:
            self.state['files'] = SystemConfigFiles(self.conf)
            self.files.paths = value

    @property
    def conf_file(self):
        if 'conf_file' not in self.state:
            self.conf_file = None

        return self.state['conf_file']

    @conf_file.setter
    def conf_file(self, value):
        pass

    @property
    def branched(self):
        return self.conf.project.branched

    @branched.setter
    def branched(self, value):
        logger.warning('branched state is stored in system not project.')

    @property
    def dependency_cache(self):
        if 'dependency_cache' not in self.state:
            self.dependency_cache = None

        return self.state['dependency_cache']

    @dependency_cache.setter
    def dependency_cache(self, value):
        if value is not None:
            self.state['dependency_cache'] = value
        else:
            p = [ self.conf.paths.projectroot, self.conf.paths.branch_output ]
            if self.conf.project.edition is None:
                p.append('dependencies.json')
            else:
                p.append('dependencies-' + self.conf.project.edition + '.json')

            self.state['dependency_cache'] = os.path.sep.join(p)

class SystemToolsConfig(ConfigurationBase):
    @property
    def pinned(self):
        return self.state['pinned']

    @pinned.setter
    def pinned(self, value):
        if isinstance(value, bool):
            self.state['pinned'] = value
        else:
            raise TypeError

    @property
    def ref(self):
        return self.state['ref']

    @ref.setter
    def ref(self, value):
        if value in ('HEAD', 'master') or len(value) == 40:
            self.state['ref'] = value
        else:
            raise TypeError

class SystemMakeConfig(ConfigurationBase):
    @property
    def generated(self):
        return self.state['generated']

    @generated.setter
    def generated(self, value):
        if isinstance(value, list):
            self.state['generated'] = value
        else:
            raise TypeError

    @property
    def static(self):
        return self.state['static']

    @static.setter
    def static(self, value):
        if isinstance(value, list):
            self.state['static'] = value
        else:
            raise TypeError

class SystemConfigFiles(RecursiveConfigurationBase):
    def __init__(self, conf):
        super(SystemConfigFiles, self).__init__(None, conf)

    @property
    def paths(self):
        return self.state['paths']

    @paths.setter
    def paths(self, value):
        if isinstance(value, list):
            self.state['paths'] = value
        else:
            raise TypeError

    @property
    def data(self):
        if 'data' not in self.state:
            self.data = self.conf.system.files.paths

        return self.state['data']

    @data.setter
    def data(self, value):
        if 'data' not in self.state:
            self.state['data'] = SystemConfigData(value, self.conf)

class SystemConfigData(RecursiveConfigurationBase):
    ## There shouldn't be any setters in this class. All items in this class
    ## must exist in SystemConfigPaths() objects.

    def __init__(self, obj, conf):
        super(SystemConfigData, self).__init__(None, conf)
        for fn in self.conf.system.files.paths:
            if isinstance(fn, dict):
                attr_name = fn.keys()[0]
            else:
                attr_name = os.path.splitext(fn)[0]

            self._option_registry.append(attr_name)
            setattr(self, attr_name, fn)

    def __getattr__(self, key):
        try:
            return object.__getattr__(self, key)
        except AttributeError as e:
            if key in self._option_registry:
                if isinstance(self.state[key], list):
                    return self.state[key]
                elif isinstance(self.state[key], dict):
                    if len(self.state[key]) == 1:
                        self._load_file(self.state[key])
                    else:
                        return self.state[key]
                else:
                    self._load_file(self.state[key])

                return self.state[key]
            else:
                logger.debug('key {0} in system data object does not exist'.format(key))
                raise e

    def __contains__(self, value):
        return value in self._option_registry

    def ingest(self, file_list=None):
        # this needs to be a noop, because some of the base constructors call
        # it, but we want this class to load data lazily.
        pass

    def _load_file(self, fn):
        if isinstance(fn, dict):
            if len(fn) > 1:
                raise TypeError
            else:
                key, fn = fn.items()[0]
                basename = key
        else:
            basename = os.path.splitext(fn)[0]

        if fn.startswith('/'):
            full_path = os.path.join(self.conf.paths.projectroot, fn[1:])
        else:
            full_path = os.path.join(self.conf.paths.projectroot,
                                     self.conf.paths.builddata, fn)

        if os.path.exists(full_path):
            # TODO we should make this process lazy with a more custom getter/setter
            self.state[basename] = self._resolve_config_data(full_path)
            logger.debug('set sub-config {0} with data from {0}'.format(basename, full_path))
        else:
            self.state[basename] = []
            logger.warning('{0} does not exist. continuing.'.format(full_path))

    @staticmethod
    def _resolve_config_data(fn):
        logger.debug('resolving config data from file ' + fn)
        if fn is None:
            return []
        else:
            data = ingest_yaml_list(fn)
            if len(data) == 1:
                return data[0]
            else:
                return data
