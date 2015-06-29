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
import os
import os.path
import sys
import yaml

import multiprocessing

from libgiza.git import GitError
from libgiza.config import ConfigurationBase
from giza.config.sphinx_config import avalible_sphinx_builders
from giza.config.error import ConfigurationError
from giza.tools.colorformatter import ColorFormatter

logger = logging.getLogger('giza.config.runtime')


class RuntimeStateConfigurationBase(ConfigurationBase):
    def __init__(self, obj=None):
        super(RuntimeStateConfigurationBase, self).__init__(obj)
        self._conf = None

    @property
    def conf(self):
        if self._conf is None:
            raise ConfigurationError
        else:
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
        if callable(value):
            self.state['_entry_point'] = value
        else:
            raise TypeError

    def get_function(self):
        return self.state['_entry_point']

    @property
    def force(self):
        if 'force' in self.state:
            return self.state['force']
        else:
            return False

    @force.setter
    def force(self, value):
        if isinstance(value, bool):
            self.state['force'] = value
        else:
            raise TypeError(type(value), value)

    @property
    def serial(self):
        if 'serial' in self.state:
            return self.state['serial']
        else:
            return False

    @serial.setter
    def serial(self, value):
        if isinstance(value, bool):
            self.state['serial'] = value
        else:
            raise TypeError

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

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # We only want the log file to represent the most recent run.
        try:
            os.unlink('giza.log')
        except OSError:
            pass

        file_logger = logging.FileHandler('giza.log', mode='wx')
        file_logger.setLevel(logging.DEBUG)
        file_logger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))

        console_logger = logging.StreamHandler()
        console_logger.setLevel(levels[value])
        console_logger.setFormatter(ColorFormatter(color=os.isatty(sys.stdout.fileno())))

        root_logger.addHandler(file_logger)
        root_logger.addHandler(console_logger)

        self.state['level'] = value

        logger.debug('set logging level to: ' + value)

    @property
    def fast(self):
        if 'fast_and_loose' not in self.state:
            return False
        else:
            return self.state['fast_and_loose']

    @fast.setter
    def fast(self, value):
        if isinstance(value, bool):
            self.state['fast_and_loose'] = value
        else:
            logger.warning('invalid option for "fast" build option')

    @property
    def runner(self):
        if 'runner' not in self.state:
            self.runner = None

        return self.state['runner']

    @runner.setter
    def runner(self, value):
        supported_runners = ['process', 'thread', 'event', 'serial']

        if value is None:
            self.state['runner'] = 'process'
        elif value in supported_runners:
            self.state['runner'] = value
        else:
            m = '{0} is not a supported runner type, choose from: {1}'.format(value,
                                                                              supported_runners)
            logger.error(m)
            raise TypeError(m)

    @property
    def pool_size(self):
        if 'pool_size' not in self.state:
            try:
                self.state['pool_size'] = multiprocessing.cpu_count()
            except:
                self.state['pool_size'] = 1

        return self.state['pool_size']

    @pool_size.setter
    def pool_size(self, value):
        if value == 1:
            self.serial = True
        elif value <= 0:
            raise TypeError('invalid pool size value: ' + value)
        else:
            self.state['pool_size'] = value

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
            raise RuntimeError('cannot locate config file')


class RuntimeStateConfig(RuntimeStateConfigurationBase):
    _option_registry = ['serial', 'length', 'days_to_save',
                        'git_branch', 'make_target',
                        'git_sign_patch', 'package_path',
                        'clean_generated', 'include_mask', 'push_targets',
                        'dry_run', 't_corpora_config', 't_translate_config',
                        't_output_file', 't_source', 't_target', 'port',
                        "changelog_version"]

    def __init__(self, obj=None):
        super(RuntimeStateConfig, self).__init__(obj)
        self._branch_conf = None

    @property
    def serial_sphinx(self):
        if 'serial_sphinx' in self.state:
            return self.state['serial_sphinx']
        else:
            return None

    @serial_sphinx.setter
    def serial_sphinx(self, value):
        if value is False:
            pass
        else:
            self.state['serial_sphinx'] = value

    @property
    def conf_path(self):
        if 'conf_path' not in self.state:
            self.conf_path = None

        return self.state['conf_path']

    @conf_path.setter
    def conf_path(self, value):
        if value is not None and os.path.isfile(value):
            self.state['conf_path'] = value
        else:
            self._discover_conf_file('build_conf.yaml')

    @property
    def language(self):
        if 'language' not in self.state:
            return 'en'
        else:
            return self.state['language']

    @language.setter
    def language(self, value):
        self.state['language'] = value

    @property
    def edition(self):
        if 'edition' not in self.state:
            return None
        else:
            return self.state['edition']

    @edition.setter
    def edition(self, value):
        self.state['edition'] = value

    @property
    def branch_conf(self):
        if self._branch_conf is None:
            self.branch_conf = None

        return self._branch_conf

    @branch_conf.setter
    def branch_conf(self, value):
        fn = os.path.join(self.conf.paths.global_config, '-'.join([self.conf.project.name,
                                                                   'published', 'branches.yaml']))

        if os.path.isfile(fn):
            with open(fn, 'r') as f:
                self._branch_conf = yaml.load(f)
        else:
            logger.warning('this project does uses legacy published branch configuration.')

            fn = os.path.join(self.conf.paths.builddata, 'published_branches.yaml')
            fq_fn = os.path.join(self.conf.paths.projectroot, fn)

            if self.conf.git.branches.current == 'master' and not os.path.isfile(fq_fn):
                self._branch_conf = {}
            else:
                try:
                    data = self.conf.git.repo.branch_file(path=fn, branch='master')
                except GitError:
                    logger.critical('giza does not support "detached head" state, '
                                    'and local repositories without a master branch.')
                    self._branch_conf = {}
                    return

                self._branch_conf = yaml.load(data)

    @property
    def builder(self):
        if 'builder' not in self.state:
            return []
        elif 'publish' in self.state['builder']:
            self.fast = False
            self.state['builder'].remove('publish')

            if 'integration' in self.conf.system.files.data:
                targets = self.conf.system.files.data.integration['base']['targets']
                self.state['builder'].extend(set([target.split('-')[0] for target in targets
                                                  if '/' not in target and
                                                  not target.startswith('htaccess')]))
                return self.state['builder']
            else:
                m = 'Builder integration not specified for "publish" target'
                logger.error(m)
                raise TypeError(m)
        else:
            return self.state['builder']

    @builder.setter
    def builder(self, value):
        if not isinstance(value, list):
            value = [value]

        for idx, builder in enumerate(value):
            if builder.startswith('pdf'):
                builder = 'latex'
                value[idx] = builder

            if builder not in avalible_sphinx_builders():
                raise TypeError("{0} is not a valid builder".format(builder))

        self.state['builder'] = value

    def is_publish_target(self):
        if 'builder' not in self.state:
            return False
        elif 'publish' in self.state['builder']:
            return True
        else:
            return False

    @property
    def git_objects(self):
        return self.state['git_objects']

    @git_objects.setter
    def git_objects(self, value):
        if isinstance(value, list):
            self.state['git_objects'] = value
        else:
            self.state['git_objects'] = [value]

    @property
    def editions_to_build(self):
        return self.state['editions_to_build']

    @editions_to_build.setter
    def editions_to_build(self, value):
        if value == [] or value is None:
            self.state['editions_to_build'] = [None]
        elif isinstance(value, list):
            self.state['editions_to_build'] = value
        else:
            self.state['editions_to_build'] = [value]

    @property
    def languages_to_build(self):
        return self.state['languages_to_build']

    @languages_to_build.setter
    def languages_to_build(self, value):
        if value == [] or value is None:
            self.state['languages_to_build'] = [None]
        elif isinstance(value, list):
            self.state['languages_to_build'] = value
        else:
            self.state['languages_to_build'] = [value]

    @property
    def dry_run(self):
        if 'dry_run' not in self.state:
            return False
        else:
            return self.state['dry_run']

    @dry_run.setter
    def dry_run(self, value):
        if value in (True, False):
            self.state['dry_run'] = value
        else:
            raise TypeError

    @property
    def t_protected_regex(self):
        return self.state['t_protected_regex']

    @t_protected_regex.setter
    def t_protected_regex(self, value):
        if value is not None:
            value = os.path.expanduser(value)
            if os.path.isfile(value):
                self.state['t_protected_regex'] = value
            else:
                raise TypeError(value + ' is not a file')
        else:
            self.state['t_protected_regex'] = None

    @property
    def t_input_file(self):
        return self.state['t_input_file']

    @t_input_file.setter
    def t_input_file(self, value):
        if value is not None:
            if os.path.exists(value):
                self.state['t_input_file'] = value
            else:
                raise TypeError(value + ' does not exist')
        else:
            self.state['t_input_file'] = None

    @property
    def t_input_files(self):
        return self.state['t_input_files']

    @t_input_files.setter
    def t_input_files(self, value):
        if value is not None:
            for path in value:
                if os.path.exists(path) is False:
                    raise TypeError(path + ' does not exist')
            self.state['t_input_files'] = value
        else:
            self.state['t_input_files'] = []

    @property
    def quickstart_git(self):
        if 'quickstart_git' in self.state:
            return self.state['quickstart_git']
        else:
            return False

    @quickstart_git.setter
    def quickstart_git(self, value):
        if isinstance(value, bool):
            self.state['quickstart_git'] = value
        else:
            self.state['quickstart_git'] = bool(value)
