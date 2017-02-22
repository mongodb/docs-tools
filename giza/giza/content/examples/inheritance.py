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

"""
Defines the ways that example content can inherit content from other
examples. This module holds two classes: a representation of a single file that
contains a set of examples and

See :mod:`giza.inheritance`
"""

import logging

from giza.libgiza.inheritance import InheritableContentError
from giza.content.examples.models import ExampleData, ExampleCase
from giza.inheritance import DataContentBase, DataCache

logger = logging.getLogger('giza.content.examples.inheritance')

# Example specific inheritance machinery


class ExampleError(InheritableContentError):
    pass


class ExampleFile(DataContentBase):

    """
    There is a one to one mapping of example files and output examples. Each
    example file has some "starting data," or a "collection" and then a sequence
    of operation and result pairs (i.e. "examples") that contain both a sequence
    of operations *and* an expected result. Each example *must* have a
    collection, and typically has 1 or more output examples.

    The ``ingest()`` method adds a check to ensure to produce an error to ensure
    that there's a "collection" value, while ``add()`` and ``fetch()`` capture
    collection and examples separately.
    """

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
        l = []
        for ref in self.ordering:
            example = self.fetch(ref)
            if 'collection' not in example:
                l.append(example)

        return l

    def add(self, doc):
        if 'collection' in doc:
            self.collection = ExampleData(doc, self.conf)

            if not self.collection.is_resolved():
                self.collection.resolve(self.data)

            return self.collection
        else:
            op = ExampleCase(doc, self.conf)
            if 'edition' in op:
                op.ref = '-'.join((str(op.ref), op.edition))

            if op.ref in self.content:
                m = 'example named {0} already exists'.format(op.ref)
                logger.error(m)
                raise ExampleError(m)
            else:
                self.content[op.ref] = op
                if not op.is_resolved():
                    op.resolve(self.data)
                logger.debug('added operation {0}'.format(op.name))

            return op

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
    content_type = 'examples'

    def file_iter(self):
        for fn in self.cache:
            data = self.cache[fn]

            if data.collection is None or data.collection.options.base_file is True:
                continue

            yield fn, data
