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

from pharaoh.config.base import ConfigurationBase

logger = logging.getLogger('pharaoh.config.runtime')


class RuntimeStateConfigurationBase(ConfigurationBase):
    def __init__(self, obj=None):
        super(RuntimeStateConfigurationBase, self).__init__(obj)
        self._conf = None

    @property
    def conf(self):
        return self._conf

    @conf.setter
    def conf(self, value):
        if isinstance(value, ConfigurationBase):
            self._conf = value
        else:
            m = 'invalid configuration object: {0}'.format(value)
            m.error(m)
            raise TypeError(m)

    @property
    def function(self):
        return self.state['_entry_point']

    @function.setter
    def function(self, value):
        self.state['_entry_point'] = value

    @property
    def level(self):
        if 'level' not in self.state:
            return 'info'
        else:
            return self.state['level']

    @level.setter
    def level(self, value):
        levels = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.critical
        }
        if value not in levels:
            value = 'info'

        logging.basicConfig()
        rlogger = logging.getLogger()

        rlogger.setLevel(levels[value])
        self.state['level'] = levels[value]

        logger.debug('set logging level to: ' + value)

    def _discover_conf_file(self, conf_file_name):
        cur = os.path.abspath(os.getcwd())
        home_path = os.path.expanduser(os.path.join('~', conf_file_name))

        if 'conf_path' not in self.state:
            self.state['conf_path'] = None

        # first look for files in likely default places:
        if 'config' in os.listdir(cur):
            fq_conf_file = os.path.join(cur, 'config', conf_file_name)
            if os.path.exists(fq_conf_file):
                self.state['conf_path'] = fq_conf_file
                return True
        elif os.path.exists(home_path):
            self.state['conf_path'] = home_path
            return True

        # now we'll try crawling up the directory tree to find the file
        cur = cur.split(os.path.sep)
        for i in range(len(cur)):
            current_attempt = os.path.sep + os.path.join(*cur[:len(cur) - i])

            contents = os.listdir(current_attempt)

            if conf_file_name in contents:
                fq_conf_file = os.path.join(current_attempt, conf_file_name)
                self.state['conf_path'] = fq_conf_file
                break
            elif 'config' in contents:
                fq_conf_file = os.path.join(current_attempt, 'config', conf_file_name)
                if os.path.exists(fq_conf_file):
                    self.state['conf_path'] = fq_conf_file
                    break

        # If we couldn't find a config file, throw an error.
        if self.state['conf_path'] is None:
            m = 'cannot locate config file'
            logger.error(m)
            raise OSError(m)

class RuntimeStateConfig(RuntimeStateConfigurationBase):
    _option_registry = ['po_files', 'host', 'port', 'db_name', 'all',
                        'username', 'status']

    def __init__(self, obj=None):
        super(RuntimeStateConfig, self).__init__(obj)
        self._branch_conf = None

    @property
    def conf_path(self):
        if 'conf_path' not in self.state:
            self.conf_path = None

        return self.state['conf_path']

    @conf_path.setter
    def conf_path(self, value):
        if value is not None and os.path.exists(value):
            self.state['conf_path'] = value
        else:
            self._discover_conf_file('build_conf.yaml')

    @property
    def source_language(self):
        if 'source_language' not in self.state:
            return 'en'
        else:
            return self.state['source_language']

    @source_language.setter
    def source_language(self, value):
        if value is not None and value not in ['en']:
            raise TypeError(value + ' is not a valid source language')
        self.state['source_language'] = value

    @property
    def target_language(self):
        return self.state['target_language']

    @target_language.setter
    def target_language(self, value):
        if value is not None and value not in ['en', 'es', 'he']:
            raise TypeError(value + ' is not a valid target language')
        self.state['target_language'] = value
