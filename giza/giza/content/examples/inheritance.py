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

logger = logging.getLogger('giza.inheritance')

from giza.serialization import ingest_yaml_list
from giza.config.base import RecursiveConfigurationBase
from giza.inheritance import InheritableContentError, DataContentBase, DataCache
from giza.content.examples.models import ExampleCollection, ExampleOperation
# from giza.content.examples.inheritance import ExampleFile

# Example specific inheritance machinery

class ExampleError(Exception): pass

class ExampleFile(DataContentBase):
    def __init__(self, src, data, conf):
        super(ExampleFile, self).__init__(src, data, conf)
        self.ingest(src)

    def ingest(self, src):
        if not isinstance(src, list) and os.path.exists(src):
            src = ingest_yaml_list(src)

        for doc in src:
            self.add(doc)

        if self.collection is None:
            m = 'all examples must have a collection'
            logger.error(m)
            raise InheritableContentError(m)

    @property
    def collection(self):
        if 'collection' not in self.state:
            return None
        else:
            return self.content[self.state['collection']]

    @collection.setter
    def collection(self, value):
        if 'collection' in self.state:
            m = 'example spec "{0}" already exists'.format(self.collection.name)
            logger.error(m)
            raise ExampleError(m)
        elif isinstance(value, ExampleCollection):
            self.content[value.name] = value
            self.state['collection'] = value.name
        else:
            raise TypeError

    def get_content_only(self):
        return { k:v for k,v in self.content.items() if 'collection' not in v }

    def add(self, doc):
        if 'collection' in doc:
            self.collection = ExampleCollection(doc, self.conf)

            if not self.collection.is_resolved():
                self.collection.resolve(self.data)
        elif 'operation' in doc:
            op = ExampleOperation(doc, self.conf)
            if op.ref in self.content:
                m = 'example named {0} already exists'.format(op.ref)
                logger.error(m)
                raise ExampleError(m)
            else:
                self.content[op.ref] = op
                if not op.is_resolved():
                    op.resolve(self.data)

                logger.debug('added operation {0}'.format(op.name))

    def fetch(self, ref):
        if ref == self.collection.name:
            if not self.collection.is_resolved():
                self.collection.resolve(self.data)

            return self.collection

        elif ref in self.content:
            content = self.content[ref]

            if not content.is_resolved():
                content.resolve(self.data)

            return content

        else:
            m = 'content with ref "{0}" not found'.format(ref)
            logger.error(m)
            raise ExampleError(m)

class ExampleDataCache(DataCache):
    content_class = ExampleFile
