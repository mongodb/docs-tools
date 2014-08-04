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

from giza.serialization import ingest_yaml_list
from giza.config.base import RecursiveConfigurationBase

class InheritableContentError(Exception): pass

class DataContentBase(RecursiveConfigurationBase):
    def __init__(self, src, data, conf):
        self._state = { 'content': { } }
        self._content = self._state['content']
        self._conf = None
        self.conf = conf
        self.data = data

    def __contains__(self, value):
        if value in self.content:
            return True
        else:
            return False

    @property
    def content(self):
        return self.state['content']

    @content.setter
    def content(self, value):
        logger.warning('cannot set content record directly')

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        if isinstance(value, DataCache):
            self._data = value
        else:
            logger.warning('cannot use invalid data cache instance.')

    def ingest(self, src):
        if not isinstance(src, list) and os.path.exists(src):
            src = ingest_yaml_list(src)

        for doc in src:
            self.add(doc)

    def add(self, doc):
        if doc.ref not in self.content:
            self.content[doc.ref] = doc
        else:
            m = 'content named {0} already exists'.format(doc.ref)
            logger.error(m)
            raise InheritableContentError(m)

    def fetch(self, ref):
        if ref in self.content:
            content = self.content[ref]

            if not content.is_resolved():
                content.resolve(self.data)

            return content
        else:
            m = 'content with ref "{0}" not found'.format(ref)
            logger.error(m)
            raise InheritableContentError(m)

    def is_resolved(self):
        unresolved = [ 1 for exmp in self.content.values()
                       if not exmp.is_resolved() ]

        if sum(unresolved) > 0:
            return False
        else:
            return True

    def resolve(self):
        for exmp in self.content.values():
            exmp.resolve(self.data)

class DataCache(RecursiveConfigurationBase):
    content_class = DataContentBase

    def __init__(self, files, conf):
        self._cache = {}
        self._conf = conf
        self.ingest(files)

    @property
    def cache(self):
        return self._cache

    @cache.setter
    def cache(self, value):
        logger.warning('cannot set cache record directly')

    def __contains__(self, key):
        return key in self.cache

    def _clear_cache(self, fn):
        self.cache[fn] = []

    def ingest(self, files):
        setup = [ self._clear_cache(fn)
                  for fn in files
                  if fn not in self.cache ]

        logger.debug('setup cache for {0} files'.format(len(setup)))

        for fn in files:
            self.add_file(fn)

    def add_file(self, fn):
        if fn not in self.cache or self.cache[fn] == []:
            data = ingest_yaml_list(fn)
            self.cache[fn] = self.content_class(data, self, self.conf)
        else:
            logger.info('populated file {0} exists in the cache'.format(fn))

    def fetch(self, fn, ref):
        if fn not in self.cache:
            logger.error('file "{0}" is not included.'.format(fn))
            raise InheritableContentError

        return self.cache[fn].fetch(ref)

class InheritableContentBase(RecursiveConfigurationBase):
    _option_registry = ['pre', 'post', 'ref', 'title', 'edition']

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
            return self.source.resolved

    def resolve(self, data):
        if (not self.is_resolved() and
            self.source.resolved in (False, None) and
            self.source.file in data):
            try:
                base = data.fetch(self.source.file, self.source.ref)
                base.resolve(data)

                base.state.update(self.state)
                self.state.update(base.state)
                self.source.resolved = True
                return True
            except InheritableContentError as e:
                logger.error(e)

        if self.source is not None and self.source.resolved is False:
            m = 'cannot find {0} and ref {1} do not  exist'.format(self.source.file, self.source.ref)
            logger.error(m)
            raise InheritableContentError(m)

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
                             self.conf.paths.includes, value) ]

        for fn in fns:
            if os.path.exists(fn):
                self.state['file'] = fn
                break

        if 'file' not in self.state:
            raise TypeError('file named {0} does not exist'.format(value))
