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

logger = logging.getLogger('giza.content.examples.inheritance')

class ExampleData(RecursiveConfigurationBase):
    def __init__(self, files, conf):
        self.cache = {}
        self._conf = None

        self.ingest(files)

    def __contains__(self, key):
        return key in self.cache
    
    def ingest(self, files):
        setup = [ self.cache[fn] = [] 
                  for fn in files
                  if fn not in self.cache ]

        logger.debug('setup cache for {0} files'.format(len(setup)))

        for fn in files:
            self.add_file(fn)

    def add_file(self, fn):
        if fn not in self.cache or self.cache[fn] == []:
            data = ingest_yaml_doc(fn)
            self.cache[fn] = ExampleFile(data, self, conf)
        else:
            logger.info('file {0} exists in the cache'.format(fn))
        
    def fetch_ref(self, fn, ref):
        if fn not in self.cache:
            self.add_file(fn)

        return self.cache[fn].fetch(ref)

class ExampleFile(RecursiveConfigurationBase):
    def __init__(self, src, data, conf):
        self.collection = None
        self.examples = {}
        self._conf = None
        self._has_inheritance = False
        self.conf = conf
        self.data = data
        self.ingest(src)

    def __contains__(self, value):
        if value in self.examples or value == self.collection.name:
            return True
        else:
            return False

    def ingest(self, src):
        for doc in src:
            self.add(src)

        if self.collection is None:
            m = 'all examples must have a collection'
            logger.error(m)
            raise ExampleError(m)

    def add(self, doc):
        if 'collection' in doc:
            if self.collection is None:
                self.collection = ExampleCollection(doc, self.conf)
                if not self.collection.is_resolved(): 
                    self.collection.resolve(self.data)
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
                if not op.is_resolved():
                    op.resolve(self.data)

                logger.debug('added operation {0}'.format(op.name))

    def fetch_ref(self, ref):
        if ref == self.collection.name:
            if not self.collection.is_resolved(): 
                self.collection.resolve(self.data)

            return self.colection

        elif ref in self.examples: 
            content = self.examples[ref]

            if not content.is_resolved():
                content.resolve(self.data)

            return content

        else: 
            m = 'content with ref "{0}" not found'.format(ref)
            logger.error(m)
            raise ExampleError(m)

    def is_resolved(self):
        if self.collection.is_resolved() is False:
            return False
        else:
            unresolved = [ 1 for exmp in self.examples.values()
                           if not exmp.is_resolved() ]

            if sum(unresolved) > 0:
                return False
            else: 
                return True 

    def resolve(self):
        self.collection.resolve(self.data)

        for exmp in self.examples.values():
            exmp.resolve(self.data)

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

    def resolve(self, data):
        if (not self.is_resolved() and 
            self.source.resolved is False and
            self.source.file in data):
            try: 
                base = data.fetch_ref(self.source.file, self.source.ref)
                base.ingest(self.state)

                self.ingest(base)
                self.source.resolved = True

                return True
            except ExampleError as e:
                logger.error(e)

        if self.source.resolved is False:
            m = 'cannot find {0} and ref {1} do not  exist'.format(self.source.file, self.source.ref)
            logger.error(m)
            raise ExampleError(m)
