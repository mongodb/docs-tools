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

import os.path
import logging

from libgiza.config import ConfigurationBase

from giza.config.assets import AssetsConfig
from giza.config.project import ProjectConfig
from giza.config.paths import PathsConfig
from giza.config.git import GitConfig
from giza.config.system import SystemConfig
from giza.config.runtime import RuntimeStateConfig
from giza.config.version import VersionConfig
from giza.config.deploy import DeployConfig
from giza.config.test import TestConfig

logger = logging.getLogger('giza.config.main')


class Configuration(ConfigurationBase):

    @property
    def project(self):
        return self.state['project']

    @project.setter
    def project(self, value):
        self.state['project'] = ProjectConfig(value, self)

    @property
    def paths(self):
        return self.state['paths']

    @paths.setter
    def paths(self, value):
        self.state['paths'] = PathsConfig(value, self)

    @property
    def git(self):
        if 'git' not in self.state:
            self.git = None

        return self.state['git']

    @git.setter
    def git(self, value):
        c = GitConfig(obj=value, repo=self.paths.projectroot, conf=self)
        self.state['git'] = c

    @property
    def runstate(self):
        return self.state['runstate']

    @runstate.setter
    def runstate(self, value):
        if isinstance(value, RuntimeStateConfig):
            if 'runstate' in self.state:
                self.state['runstate'].state.update(value.state)
            else:
                value.conf = self
                self.state['runstate'] = value
        elif isinstance(value, dict):
            if 'runstate' in self.state:
                self.state['runstate'].ingest(value)
            else:
                runtime = RuntimeStateConfig(value)
                runtime.conf = self
                self.state['runstate'] = runtime
        elif value is None:
            runtime = RuntimeStateConfig()
            runtime.conf = self
            self.state['runstate'] = runtime
        else:
            msg = "invalid runtime state"
            logger.critical(msg)
            raise TypeError(msg)

    @property
    def version(self):
        if 'version' not in self.state:
            self.version = None

        return self.state['version']

    @version.setter
    def version(self, value):
        self.state['version'] = VersionConfig(value, self)

    @property
    def system(self):
        if 'system' not in self.state:
            self.system = None

        return self.state['system']

    @system.setter
    def system(self, value):
        self.state['system'] = SystemConfig(value, self)

    @property
    def assets(self):
        if 'assets' in self.state:
            return self.state['assets']
        else:
            return None

    @assets.setter
    def assets(self, value):
        if isinstance(value, list):
            self.state['assets'] = [AssetsConfig(v) for v in value]
        else:
            self.state['assets'] = [AssetsConfig(value)]

    @property
    def deploy(self):
        if 'deploy' not in self.state:
            self.deploy = None
        return self.state['deploy']

    @deploy.setter
    def deploy(self, value):
        fn = os.path.join(self.paths.projectroot, self.paths.global_config, 'deploy.yaml')
        if os.path.exists(fn):
            self.state['deploy'] = DeployConfig(fn)
        else:
            self.state['deploy'] = {}

    @property
    def test(self):
        if 'test' not in self.state:
            self.test = None
        return self.state['test']

    @test.setter
    def test(self, value):
        fn = os.path.join(self.paths.projectroot, self.paths.global_config, 'test-matrix.yaml')
        if os.path.exists(fn):
            self.state['test'] = TestConfig(fn)
        else:
            self.state['test'] = {}
