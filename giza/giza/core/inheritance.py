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
:mod:`~giza.inheritance` is a library for managing content reuse using an
inheritance-based model for structured content. In systems that use this code,
writers define content in a structured form, where content units can "inherit"
from other content units and optionally override some portions of the inherited
units.
"""

import copy
import collections
import logging
import os.path
import sys

logger = logging.getLogger('giza.core.inheritance')

from jinja2 import Template

from giza.config.base import RecursiveConfigurationBase, ConfigurationBase
from giza.tools.serialization import ingest_yaml_list
from giza.content.helper import level_characters, edition_check

if sys.version_info >= (3, 0):
    basestring = str

class InheritableContentError(Exception):
    """
    Exception used by inheritance code to indicate a problem resolving
    inherited content.
    """

    pass

class InheritableContentBase(RecursiveConfigurationBase):
    """
    Base data object that represents a single unit of content. Typically
    sub-classed.
    """

    _option_registry = ['pre', 'post', 'final', 'ref', 'content', 'edition']

    @property
    def replacement(self):
        if 'replacement' not in self.state:
            self.replacement = {}

        return self.state['replacement']

    @replacement.setter
    def replacement(self, value):
        if 'replacement' not in self.state:
            self.state['replacement'] = {}

        if isinstance(value, dict):
            value_iter = value.items()
        elif isinstance(value, collections.Iterable):
            for item in value:
                if len(item) != 2:
                    raise TypeError
            value_iter = value
        else:
            raise TypeError

        for k, v in value_iter:
            self.state['replacement'][k] = v

    @property
    def title(self):
        return self.state['title']

    @title.setter
    def title(self, value):
        if isinstance(value, basestring):
            self.state['title'] = TitleData({'text': value})
        elif isinstance(value, TitleData):
            self.state['title'] = value
        elif isinstance(value, dict):
            self.state['title'] = TitleData(value)
        else:
            raise TypeError

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
            try:
                return self.source.resolved
            except AttributeError:
                return False

    def _is_resolveable(self, data):
        try:
            return not self.is_resolved() and self.source.file in data.cache
        except AttributeError:
            logger.warning(str(data) + ' is not resolvable')
            return False

    def has_field(self, name):
        if name in self and getattr(self, name, None) is not None:
            return True
        else:
            return False

    def resolve(self, data):
        if self._is_resolveable(data):
            try:
                base = data.fetch(self.source.file, self.source.ref)
                base.resolve(data)

                needs_replacement = self.replacement != base.replacement

                if needs_replacement:
                    replacement = copy.deepcopy(base.replacement)
                    replacement.update(self.replacement)

                base.state.update(self.state)
                self.state.update(base.state)

                if needs_replacement:
                    self.replacement = replacement

                self.source.resolved = True
                return True
            except InheritableContentError as e:
                logger.error(e)

        if not self.is_resolved():
            m = 'cannot find {0} and ref "{1}" do not exist'.format(self.source.file, self.source.ref)
            logger.error(m)
            raise InheritableContentError(m)

    def render(self):
        if self.replacement:
            attempts = range(10)

            for key in self.state.keys():
                if isinstance(self.state[key], collections.Iterable):
                    should_resplit = None

                    if isinstance(self.state[key], list):
                        for it in self.state[key]:
                            if not isinstance(it, basestring):
                                should_resplit = False
                        if should_resplit is None:
                            should_resplit = True
                            self.state[key] = '\n'.join(self.state[key])

                    for i in attempts:
                        if '{{' not in self.state[key]:
                            break

                        template = Template(self.state[key])
                        self.state[key] = template.render(**self.replacement)

                        if '{{' not in self.state[key]:
                            break

                    if should_resplit is True:
                        self.state[key] = self.state[key].split('\n')
                elif isinstance(self.state[key], InheritableContentBase):
                    if len(self.state[key].replacement) == 0:
                        self.state[key].replacement = self.replacement

                    self.state[key].render()


class InheritanceReference(RecursiveConfigurationBase):
    """
    Represents a single reference to another unit of content. The
    setter method for the :meth:`~giza.inheritance.InheritanceReference.file`
    attribute, returns an error if it cannot discover a specified value.
    """

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

    def is_resolved(self):
        return self.resolved

    @property
    def file(self):
        return self.state['file']

    @file.setter
    def file(self, value):
        # if 'file' in self.state and os.path.isfile(self.state['file']):
        #     return

        fns = set([ # value,  os.path.abspath(value),
                   os.path.join(self.conf.paths.projectroot, value),
                   os.path.join(self.conf.paths.projectroot,
                                self.conf.paths.branch_includes, value),
                   # os.path.join(self.conf.paths.projectroot,
                   #              self.conf.paths.includes, value)
                                ])

        try:
            fns.add(os.path.join(self.conf.paths.projectroot,
                                 self.conf.paths.source, value))
        except KeyError:
            pass

        for fn in fns:
            if os.path.exists(fn):
                self.state['file'] = fn
                break

        if 'file' not in self.state:
            raise TypeError('file named {0} does not exist'.format(value))


##############################

class DataContentBase(RecursiveConfigurationBase):
    """
    Represents a group of units ingested from a single file.
    """

    content_class = InheritableContentBase

    def __init__(self, src, data, conf):
        self._state = { 'content': { } }
        self._content = self._state['content']
        self._conf = None
        self.conf = conf
        self.data = data
        self.ingest(src)

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
            if edition_check(doc, self.conf) is False:
                continue
            try:
                self.add(doc)
            except Exception as e:
                logger.error('could not inherit, because: ' + str(e))
                logger.info(doc)

    def add(self, doc):
        if 'ref' in doc:
            ref = doc['ref']
        elif 'source' in doc:
            ref = doc['source']['ref']
        elif 'inherit' in doc:
            ref = doc['inherit']['ref']
        else:
            ref = None

        if 'ref' not in doc and ref is not None:
            doc['ref'] = ref

        if ref not in self.content:
            if isinstance(doc, self.content_class):
                content = doc
            else:
                try:
                    content = self.content_class(doc)
                except TypeError:
                    content = self.content_class(doc, self.conf)

            if ref is not None:
                content.ref = ref

            self.content[content.ref] = content

            if not content.is_resolved():
                content.resolve(self.data)

            return content
        else:
            m = 'content named "{0}" already exists'.format(doc['ref'])
            logger.error(m)
            logger.warning(doc)
            raise InheritableContentError(m)

    def fetch(self, ref):
        if ref in self.content:
            content = self.content[ref]

            if not content.is_resolved():
                content.resolve(self)

            return copy.deepcopy(content)
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
        """Resolves all inheritance."""

        for exmp in self.content.values():
            exmp.resolve(self.data)

class DataCache(RecursiveConfigurationBase):
    """
    Represents a group of related files that hold similar kinds of structured
    data. Often subclassed.
    """

    content_class = DataContentBase

    def __init__(self, files, conf):
        self._cache = {}
        self._conf = conf
        self.ingest(files)

    def __len__(self):
        return len(self._cache)

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
            logger.debug('populated file {0} exists in the cache'.format(fn))

    def fetch(self, fn, ref):
        if fn not in self.cache:
            logger.error('file "{0}" is not included.'.format(fn))
            if os.path.isfile(fn):
                self.add_file(fn)
            else:
                raise InheritableContentError

        if self.cache[fn] == []:
            self.add_file(fn)

        return self.cache[fn].fetch(ref)

    def file_iter(self):
        for fn in self.cache:
            yield fn, self.cache[fn]

    def content_iter(self)
        for fn in self.cache:
            for data in self.cache[fn].content.values():
                yield fn, data


class TitleData(ConfigurationBase):
    _option_registry = ['text']

    @property
    def character(self):
        return self.level

    @character.setter
    def character(self, value):
        self.level = level_characters[value]

    @property
    def level(self):
        if 'level' not in self.state:
            return 3
        else:
            return self.state['level']

    @level.setter
    def level(self, value):
        if isinstance(value, int):
            self.state['level'] = value
        else:
            raise TypeError
