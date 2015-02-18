# Copyright 2015 MongoDB, Inc.
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
import sys
import os

import libgiza.config
import yaml

logger = logging.getLogger('giza.config.test')

if sys.version_info >= (3, 0):
    basestring = str


class TestConfig(libgiza.config.ConfigurationBase):
    def ingest(self, input_obj):
        if os.path.isfile(input_obj) is True:
            with open(input_obj, 'r') as f:
                input_obj = [d for d in yaml.safe_load_all(f)]
        elif isinstance(input_obj, list):
            pass
        else:
            raise RuntimeError('invalid test configuration')

        for doc in input_obj:
            self.add_project(doc)

    def add_project(self, project):
        if isinstance(project, TestProject):
            self.projects.append(project)
        else:
            self.projects.append(TestProject(project))

    @property
    def projects(self):
        if 'projects' not in self.state:
            self.projects = None
        return self.state['projects']

    @projects.setter
    def projects(self, value):
        if 'projects' not in self.state:
            self.state['projects'] = []

        if value is None:
            return
        elif isinstance(value, list):
            for proj in value:
                self.add_project(proj)
        else:
            self.add_projecct(value)

    @property
    def private_projects(self):
        for project in self.projects:
            if project.private is True:
                yield project

    @property
    def public_projects(self):
        for project in self.projects:
            if project.private is False:
                yield project


class TestProject(libgiza.config.ConfigurationBase):
    @property
    def project(self):
        return self.state['project']

    @project.setter
    def project(self, value):
        if isinstance(value, basestring):
            self.state['project'] = value
        else:
            raise TypeError(type(value), value)

    @property
    def uri(self):
        return self.state['uri']

    @uri.setter
    def uri(self, value):
        if not isinstance(value, basestring):
            raise TypeError(type(value), value)
        elif not value.endswith('.git'):
            raise TypeError('malformed uri: ' + value)

        self.state['uri'] = value

    @property
    def branches(self):
        if 'branches' not in self.state:
            return ['master']
        else:
            return self.state['branches']

    @branches.setter
    def branches(self, value):
        if isinstance(value, basestring):
            value = [value]

        if not isinstance(value, list):
            raise TypeError(type(value), value)
        else:
            for branch in value:
                if not isinstance(branch, basestring):
                    raise TypeError(type(value), value)

        self.state['branches'] = value

    @property
    def private(self):
        if 'private' in self.state:
            return self.state['private']
        else:
            return False

    @private.setter
    def private(self, value):
        if isinstance(value, bool):
            self.state['private'] = value
        else:
            self.state['private'] = bool(value)

    @property
    def root(self):
        if 'root' in self.state:
            return self.state['root']
        else:
            return None

    @root.setter
    def root(self, value):
        if isinstance(value, basestring):
            self.state['root'] = value
        else:
            raise TypeError(type(value), value)

    @property
    def operations(self):
        if 'operations' in self.state:
            return self.state['operations']
        else:
            return {}

    @operations.setter
    def operations(self, value):
        if not isinstance(value, dict):
            raise TypeError(type(value), value)

        ops = {}
        for key, op in value.items():
            ops[key] = []
            for cmd in op:
                if isinstance(cmd, basestring):
                    ops[key].append(cmd)
                elif isinstance(cmd, list):
                    ops[key].extend(cmd)

        self.state['operations'] = ops
