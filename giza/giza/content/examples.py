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

logger = logging.getLogger('giza.content.examples')

from giza.files import expand_tree
from giza.config.base import RecursiveConfigurationBase, ConfigurationBase

class ExampleError(Exception): pass

class ExampleData(RecursiveConfigurationBase):
    def __init__(self, src, conf):
        self.collection = None
        self.examples = {}
        self._conf = None
        self._has_inheritance = False
        self.conf = conf
        self.ingest(src)

    def __contains__(self, value):
        if value in self.examples or value == self.collection.name:
            return True
        else:
            return False

    def ingest(src):
        for doc in src:
            if 'collection' in doc:
                if self.collection is None:
                    self.collection = ExampleCollection(doc, self.conf)
                    if not self.collection.is_resolved():
                        self._has_inheritance = True
                else:
                    m = 'example spec "{0}" already exists'.format(self.collection.name)
                    logger.error(m)
                    raise ExampleError(m)
            elif 'operation' in doc:
                op = ExamplOperation(doc, self.conf)
                if op.ref in self.examples:
                    m = 'example named {0} already exists'.format(op.ref)
                    logger.error(m)
                    raise ExampleError(m)
                else:
                    self.examples[op.ref] = op
                    logger.debug('added operation {0}'.format(op.name))

        if self.collection is None:
            m = 'all examples must have a collection'
            logger.error(m)
            raise ExampleError(m)

    def resolve(self, data):
        self.collection.resolve(data)

        for exmp in self.example.values():
            exmp.resolve(data)


class ExampleCollection(InheritableContentBase):
    @property
    def collection(self):
        return self.state['ref']

    @collection.setter
    def collection(self, value):
        self.state['ref'] = value

    @property
    def name(self):
        return self.collection

    @property
    def ref(self):
        return self.collection

    @property
    def documents(self):
        return self.state['documents']

    @documents.setter
    def documents(self, value):
        if isinstance(value, list):
            self.state['documents'] = value
        else:
            raise TypeError('{0} is not a list'.format(value))

class ExampleOperation(InheritableContentBase):
    pass

class InheritableContentBase(RecursiveConfigurationBase)
    _option_registry = ['pre', 'post']

    @property
    def source(self):
        if 'source' in self.state:
            return self.state['source']
        else:
            return None

    @source.setter
    def source(self, value):
        self.state['source'] = InheritanceReference(value, self.conf)

    inherit = source
    def is_resolved(self):
        if self.source is None:
            return True
        else:
            return self.source.resolved()

    def resolve(self, collection):
        if self.source.resolved is False:
            if self.source.file in collection and self.source.ref in collection[self.source.file]:
                self.ingest(collection[self.source.file][self.source.ref])
                self.source.resolved = True
            else:
                m = 'source {0} and ref {1} do not  exist'.format(self.source.file, self.source.ref)
                logger.error(m)
                raise ExampleError(m)

class InheritanceReference(RecursiveConfigurationBase):
    _option_registry = ['ref']

    @property
    def resolved(self):
        if 'resolved' not in self.state:
            return False
        else:
            return self.state['resolved']

    @resolved.setter
    def resolved(self, value):
        if isinstance(value, bool):
            self.state['resolved'] = value
        else:
            raise TypeError('{0} is not boolean'.format(value))

    @property
    def file(self):
        return self.state['file']

    @file.setter
    def file(self, value):
        fns = [ value,
                os.path.join(self.conf.paths.projectroot, value),
                os.path.join(self.conf.paths.projectroot,
                             self.conf.paths.inclueds, value) ]

        for fn in fns:
            if os.path.exists(fn):
                self.state['file'] = fn
                break

        if 'file' not in self.state:
            raise TypeError('file named {0} does not exist'.format(value))

def render_example(fn, conf):
    ExampleData(fn, conf)

    logger.info('--------------------------------')
    logger.info('would have rendered example for: ' + fn)
    logger.info('--------------------------------')

def example_tasks(conf, app):
    include_dir = os.path.join(conf.paths.projectroot, conf.paths.includes)

    example_sources = [ fn for fn in
                        expand_tree(include_dir, 'yaml')
                        if fn.startswith('example') ]

    examples = { }

    for fn in example_sources:
        examples[fn] = ExampleData(fn, conf)

    for exmp in examples:
        exmp.resolve(examples)
