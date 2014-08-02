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

logger = logging.getLogger('giza.content.examples.models')

from giza.config.base import RecursiveConfigurationBase, ConfigurationBase
from giza.serialization import ingest_yaml_doc

class ExampleError(Exception): pass

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
