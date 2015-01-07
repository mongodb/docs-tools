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
from giza.config.base import ConfigurationBase
from giza.tools.files import expand_tree

###### Data Model ######

class ContentType(ConfigurationBase):
    _option_registry = ['name', 'dir']

    @property
    def sources(self):
        return [ fn for fn in
                 expand_tree(self.dir, 'yaml')
                 if fn.startswith(self.fn_prefix) ]

    @property
    def fn_prefix(self):
        return os.path.join(self.dir, self.name)

    def get_basename(self, fn):
        return fn[len(self.fn_prefix)+1:-5]

    @property
    def output_dir(self):
        if 'output_dir' in self.state:
            dirname = self.state['output_dir']
        else:
            dirname = self.name

        return os.path.join(self.dir, dirname)

    @output_dir.setter
    def output_dir(self, value):
        self.state['output_dir'] = value

    @property
    def task_generator(self):
        if '_task_generator' in self.state:
            return self.state['_task_generator']
        else:
            logger.warning('returning no-op content generator for: ' + self.name)
            def nop(*args, **kwargs): pass
            return nop

    @task_generator.setter
    def task_generator(self, value):
        if callable(value):
            self.state['_task_generator'] = value
        else:
            raise TypeError

###### Factories ######

def new_content_type(name, conf, task_generator=None, source_dir=None, output_dir=None):
    if source_dir is None:
        source_dir = os.path.join(conf.paths.projectroot,
                                  conf.paths.branch_includes)

    if output_dir is None:
        output_dir = os.path.join(source_dir, name)

    c = ContentType()
    c.name = name
    c.dir = source_dir
    c.output_dir = output_dir

    if task_generator is not None:
        c.task_generator = task_generator

    return c

###### Implementation Internals ######

class ContentRegistry(ConfigurationBase):
    def add(self, name, definition):
        if not isinstance(definition, ContentType):
            raise TypeError
        else:
            if name not in self.state:
                self._option_registry.append(name)
                self.state[name] = definition

    def iterator(self):
        return self.state.values()

    def output_directories(self, prefix_len=0):
        for content_type in self.iterator():
            yield content_type.output_dir[prefix_len:]

    @property
    def task_generators(self):
        for content in self.state.values():
            yield content, content.task_generator
