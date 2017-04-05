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

import yaml

from giza.libgiza.config import RecursiveConfigurationBase, ConfigurationBase
from giza.config.sphinx_local import SphinxLocalConfig
from giza.config.manpage import ManpageConfig
from giza.config.pdfs import PdfConfig
from giza.config.intersphinx import IntersphinxConfig
from giza.config.redirects import HtaccessData
from giza.config.content import ContentRegistry
from giza.config.replacements import ReplacementData
from giza.config.migrations import MigrationData
from giza.config.images import ImageData
from giza.config.jeerah import JeerahConfig

logger = logging.getLogger('giza.config.system')


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
            self.state['dependency_cache'] = os.path.join(self.conf.paths.projectroot,
                                                          self.dependency_cache_fn)

    @property
    def dependency_cache_fn(self):
        if 'dependency_cache_fn' not in self.state:
            self.dependency_cache_fn = None

        return self.state['dependency_cache_fn']

    @dependency_cache_fn.setter
    def dependency_cache_fn(self, value):
        if value is None:
            p = [self.conf.paths.branch_output]
            if self.conf.project.edition is None:
                p.append('dependencies.json')
            else:
                p.append('dependencies-' + self.conf.project.edition + '.json')

            self.state['dependency_cache_fn'] = os.path.sep.join(p)
        else:
            self.state['dependency_cache_fn'] = value

    @property
    def runstate(self):
        return self.conf.runstate

    @runstate.setter
    def runstate(self, value):
        self.conf.runstate = value

    @property
    def content(self):
        if 'content' not in self.state:
            self.state['content'] = ContentRegistry()

        return self.state['content']


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

    def get_configs(self, key):
        fns = []
        for value in self.conf.system.files.paths:
            if isinstance(value, dict):
                if 'migration' in value:
                    if isinstance(value[key], list):
                        fns.extend(value[key])
                    else:
                        fns.append(value[key])
            elif value.startswith(key):
                fns.append(value)

        results = []

        for fn in fns:
            if fn.startswith(os.path.sep):
                fn = fn[len(os.path.sep):]

            for new_file in [os.path.join(self.conf.paths.projectroot, fn),
                             os.path.join(self.conf.paths.projectroot,
                                          self.conf.paths.source, fn),
                             os.path.join(self.conf.paths.projectroot,
                                          self.conf.paths.builddata, fn)]:
                if os.path.isfile(new_file):
                    results.append(new_file)

        return results


class SystemConfigData(RecursiveConfigurationBase):
    # There shouldn't be any setters in this class. All items in this class
    # must exist in SystemConfigPaths() objects.

    _always_list_configs = ['errors', 'images', 'intersphinx', 'manpages',
                            'pdfs', 'push', 'robots']
    _single_document_configs = ['errors']

    def __init__(self, obj, conf):
        super(SystemConfigData, self).__init__(None, conf)
        for fn in self.conf.system.files.paths:
            if isinstance(fn, dict):
                attr_name = next(iter(fn))
            else:
                attr_name = os.path.splitext(fn)[0]

            self._option_registry.append(attr_name)
            setattr(self, attr_name, fn)

    def __getattr__(self, key):
        try:
            return object.__getattribute__(self, key)
        except AttributeError:
            pass

        if key not in self._option_registry:
            m = 'key "{0}" in system.data object does not exist'.format(key)
            if not key.startswith('__'):
                logger.debug(m)
            raise AttributeError(m)

        if isinstance(key, dict):
            basename, fn = next(iter(key.items()))
        else:
            fn = key
            basename = os.path.splitext(fn)[0]

        if isinstance(self.state[key], list):
            pass
        elif isinstance(self.state[key], dict):
            if len(self.state[key]) == 1:
                basename, fns = next(iter(self.state[key].items()))
                if isinstance(fns, list):
                    for fn in fns:
                        self._load_file(basename, fn)
                else:
                    self._load_file(basename, fn)
        else:
            self._load_file(basename, self.state[key])

        if len(self.state[key]) == 1 and key not in self._always_list_configs:
            return self.state[key][0]
        else:
            return self.state[key]

    def __contains__(self, value):
        return value in self._option_registry

    def ingest(self, file_list=None):
        # this needs to be a noop, because some of the base constructors call
        # it, but we want this class to load data lazily.
        pass

    def _load_file(self, basename, fn):
        full_path = self._resolve_config_path(fn)

        if basename not in self.state:
            if os.path.isfile(full_path):
                # TODO we should make this process lazy with a more custom getter/setter
                self.state[basename] = self._resolve_config_data(full_path, basename)
                logger.debug('set sub-config %s with data from %s', basename, full_path)
            else:
                self.state[basename] = []
                logger.warning('{0} does not exist. continuing.'.format(full_path))
        else:
            if os.path.isfile(full_path):
                d = self._resolve_config_data(full_path, basename)
            else:  # if os.path.isfile(self.state[basename]):
                full_path = self.state[basename]  # .items()[0][1]
                d = self._resolve_config_data(self._resolve_config_path(full_path), basename)
            self._set_config_data(basename, fn, d)

    def keys(self):
        return self._option_registry

    def _set_config_data(self, basename, fn, d):
        if isinstance(self.state[basename], list):
            if isinstance(d, list):
                self.state[basename].extend(d)
            else:
                self.state[basename].append(d)
        else:
            if (isinstance(self.state[basename], (ConfigurationBase, dict)) and
                    len(self.state[basename]) == 1):

                self.state[basename] = []
            elif self.state[basename] != fn:
                self.state[basename] = [self.state[basename]]
            else:
                self.state[basename] = []

            if isinstance(d, list):
                self.state[basename].extend(d)
            else:
                self.state[basename].append(d)

    def _resolve_config_path(self, fn):
        if isinstance(fn, dict):
            if len(fn) == 1:
                fn = next(iter(fn.values()))
            else:
                logger.error("unsupported config file specification: " + str(fn))

        if os.path.exists(fn):
            full_path = fn
        elif os.path.exists(os.path.join(os.getcwd(), fn)):
            full_path = os.path.join(os.getcwd(), fn)
        elif fn.startswith('/'):
            full_path = os.path.join(self.conf.paths.projectroot, fn[1:])
        else:
            full_path = os.path.join(self.conf.paths.projectroot,
                                     self.conf.paths.builddata, fn)

        return full_path

    def _resolve_config_data(self, fn, basename):
        logger.debug('resolving config data from file ' + fn)
        if fn is None:
            return []
        else:
            mapping = {
                'sphinx_local': SphinxLocalConfig,
                'sphinx-local': SphinxLocalConfig,
                'manpages': ManpageConfig,
                'pdfs': PdfConfig,
                'intersphinx': IntersphinxConfig,
            }
            # recur_mapping for config objects that subclass RecursiveConfigurationBase
            recur_mapping = {
                'jira': JeerahConfig
            }
            special_lists = {
                'htaccess': HtaccessData,
                'migrations': MigrationData,
                'images': ImageData,
            }
            self._always_list_configs.extend(special_lists.keys())

            with open(fn, 'r') as f:
                if basename in self._single_document_configs:
                    data = yaml.safe_load(f)
                else:
                    data = yaml.safe_load_all(f)

                if basename in mapping:
                    data = [mapping[basename](doc) for doc in data]
                elif basename in recur_mapping:
                    data = [recur_mapping[basename](doc, self.conf) for doc in data]
                elif basename in special_lists:
                    l = special_lists[basename]()
                    l.conf = self.conf
                    l.extend([d for d in data])
                    data = l
                elif basename == 'replacement':
                    data = ReplacementData([d for d in data], self.conf)
                    return data

                if not isinstance(data, list):
                    data = [item for item in data]

            if len(data) == 1 and (basename not in self._always_list_configs):
                return data[0]
            else:
                return data
