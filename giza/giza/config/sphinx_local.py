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

from giza.libgiza.config import ConfigurationBase

logger = logging.getLogger('giza.config.sphinx_local')


class SphinxLocalConfig(ConfigurationBase):
    _option_registry = ['project', 'master_doc', 'logo']

    @property
    def paths(self):
        return self.state['paths']

    @paths.setter
    def paths(self, value):
        if isinstance(value, dict):
            self.state['paths'] = SphinxLocalPaths(value)
        else:
            raise TypeError

    @property
    def theme(self):
        return self.state['theme']

    @theme.setter
    def theme(self, value):
        if isinstance(value, dict):
            self.state['theme'] = SphinxLocalTheme(value)
        else:
            raise TypeError

    @property
    def sidebars(self):
        return self.state['sidebars']

    @sidebars.setter
    def sidebars(self, value):
        if isinstance(value, dict):
            self.state['sidebars'] = value
        else:
            raise TypeError


class SphinxLocalPaths(ConfigurationBase):
    _option_registry = ['static', 'locale']


class SphinxLocalTheme(ConfigurationBase):
    _option_registry = ['name', 'project', 'google_analytics', 'book_path_base',
                        'repo', 'jira', 'sitename']

    @property
    def nav_excluded(self):
        return self.state['nav_excluded']

    @nav_excluded.setter
    def nav_excluded(self, value):
        if isinstance(value, list):
            for path in value:
                if not path.startswith('/'):
                    raise TypeError

            self.state['nav_excluded'] = value
        else:
            raise TypeError
