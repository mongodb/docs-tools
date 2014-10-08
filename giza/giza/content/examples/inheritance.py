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

logger = logging.getLogger('giza.content.examples.inheritance')

from giza.config.base import RecursiveConfigurationBase
from giza.content.examples.models import ExampleData, ExampleCase
from giza.core.inheritance import InheritableContentError, DataContentBase, DataCache
from giza.tools.serialization import ingest_yaml_list

# Example specific inheritance machinery

class ExampleError(Exception): pass

class ExampleFile(DataContentBase):
    def ingest(self, src):
        if not isinstance(src, list):
            if os.path.isfile(src):
                src = ingest_yaml_list(src)
            else:
                m = '{0} is not a valid example file.'
                logger.error(m)
                raise InheritableContentError(m)

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
        elif isinstance(value, ExampleData):
            self.content[value.name] = value
            self.state['collection'] = value.name
        else:
            raise TypeError

    @property
    def examples(self):
        return [ example
                 for example in self.content.values()
                 if 'collection' not in example
        ]

    def add(self, doc):
        if ('edition' in doc and
            'edition' in self.conf.project and
            doc['edition'] != self.conf.project.edition):
            return

        if 'collection' in doc:
            self.collection = ExampleData(doc, self.conf)

            if not self.collection.is_resolved():
                self.collection.resolve(self.data)
        elif 'operation' in doc:
            op = ExampleCase(doc, self.conf)
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
