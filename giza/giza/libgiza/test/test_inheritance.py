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

import os

from unittest import TestCase

from giza.libgiza.inheritance import (DataContentBase, DataCache,
                                      InheritableContentError, InheritableContentBase)

from giza.config.main import Configuration
from giza.config.runtime import RuntimeStateConfig

# these helper functions are useful in reusing these tests for the giza
# application tests.


def get_inheritance_data_files():
    return [os.path.join(get_test_file_path(), fn)
            for fn in ('example-add-one.yaml', 'example-add-two.yaml',
                       'example-add-three.yaml')]


def get_test_file_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'data-inheritance'))


class TestDataCache(TestCase):
    def setUp(self):
        self.c = Configuration()
        self.c.runstate = RuntimeStateConfig()
        self.c.paths = {'includes': get_test_file_path()}

        self.DataContentBase = DataContentBase
        self.DataCache = DataCache

        self.create_data()

    def create_data(self):
        self.files = get_inheritance_data_files()
        self.data = self.DataCache([], self.c)

    def test_content_class_default(self):
        self.assertEqual(self.data.cache, {})
        self.assertIs(self.data.content_class, self.DataContentBase)

    def test_cache_not_setable(self):
        self.assertEqual(self.data.cache, {})
        self.data.cache = []
        self.assertEqual(self.data.cache, {})

    def test_cache_property_reference(self):
        self.assertIs(self.data.cache, self.data._cache)

    def test_cache_cleaner(self):
        self.assertEqual(self.data.cache, {})

        self.data._clear_cache('foo')
        self.data._clear_cache('bar')

        self.assertIn('foo', self.data.cache)
        self.assertIn('bar', self.data.cache)

        self.assertEqual(self.data.cache['foo'], [])
        self.assertEqual(self.data.cache['bar'], [])

    def test_membership(self):
        self.assertEqual(self.data.cache, {})

        self.data._clear_cache('foo')
        self.data._clear_cache('bar')

        self.assertIn('foo', self.data.cache)
        self.assertIn('bar', self.data.cache)

        self.assertIn('foo', self.data)
        self.assertIn('bar', self.data)

    def test_ingest(self):
        self.assertEqual(self.data.cache, {})
        self.data.ingest(self.files)
        self.assertNotEqual(self.data.cache, {})

        for fn in self.files:
            self.assertIn(fn, self.data)

    def test_ingest_ignore_duplicates(self):
        self.assertEqual(self.data.cache, {})
        self.data.ingest(self.files)
        self.data.ingest(self.files)
        self.assertNotEqual(self.data.cache, {})

        self.assertEqual(len(self.data.cache), len(self.files))

    def test_add_file(self):
        self.assertEqual(self.data.cache, {})

        for fn in self.files:
            self.data.add_file(fn)
            self.assertIn(fn, self.data.cache)
            self.assertIn(fn, self.data)
            self.assertIsInstance(self.data.cache[fn], self.data.content_class)

    def test_fetch(self):
        self.assertEqual(self.data.cache, {})
        self.data.ingest(self.files)

        for fn in self.files:
            self.assertIn(fn, self.data)
            for idx in range(len(self.data.cache), 1):
                content = self.data.fetch(fn, idx)
                self.assertIsInstance(content, dict)

        self.assertEqual(len(self.data.cache), len(self.files))

    def test_fetch_without_adding_file(self):
        self.assertEqual(self.data.cache, {})

        for fn in self.files:
            if not os.path.isfile(fn):
                with self.assertRaises(InheritableContentError):
                    self.data.fetch(fn, 1)
                self.assertNotIn(fn, self.data)


class TestDataContentBase(TestCase):
    def setUp(self):
        self.c = Configuration()
        self.c.runstate = RuntimeStateConfig()
        self.c.paths = {'includes': 'data-inheritance',
                        'projectroot': os.path.abspath(os.path.dirname(__file__))}

        self.DataContentBase = DataContentBase
        self.DataCache = DataCache
        self.InheritableContentBase = InheritableContentBase

        self.dummy_doc = {'ref': 'dummy-doc',
                          'pre': 'pre text'}

        self.create_data()

    def create_data(self):
        self.content_fn = get_inheritance_data_files()[0]

        self.data = self.DataCache([self.content_fn], self.c)
        self.content = self.data.cache[self.content_fn]

    def test_content_created(self):
        for fn, example in self.data.file_iter():
            self.assertIsInstance(example, self.DataContentBase)

    def test_content_item_created(self):
        for fn, block in self.data.content_iter():
            self.assertIsInstance(block, self.InheritableContentBase)

    def test_content_is_correct_type(self):
        self.assertIsInstance(self.content, self.DataContentBase)

    def test_content_state_reference(self):
        self.assertIs(self.content.content, self.content.state['content'])

    def test_reference_to_cache(self):
        self.assertIs(self.content.data, self.data)

    def test_fetching_content(self):
        for idx in self.content.content:
            compared = self.data.fetch(self.content_fn, idx)
            for key in self.content.content[idx].state:
                self.assertEqual(self.content.content[idx].state[key], getattr(compared, key))

    def test_resolve_checker(self):
        if isinstance(self.content, dict):
            with self.assertRaises(AttributeError):
                self.content.is_resolved()
        else:
            self.assertIsInstance(self.content.is_resolved(), bool)

    def test_add_always_returns_value(self):
        cache = self.DataCache([], self.c)
        collection = cache.content_class('', cache, self.c)
        self.assertIsInstance(collection, DataContentBase)

        content = collection.add(self.dummy_doc)

        self.assertIsInstance(content, InheritableContentBase)
        print(collection.content)


class TestInheritedContentResolution(TestCase):
    def setUp(self):
        self.c = Configuration()
        self.c.runstate = RuntimeStateConfig()
        self.c.paths = {'includes': os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                                 'data-inheritance')}
        self.DataCache = DataCache

        self.create_data()

    def create_data(self):
        self.data = self.DataCache(get_inheritance_data_files(), self.c)
        self.len_source_docs = 5
        self.num_docs = 3

    def test_gross_correctness_of_ingestion(self):
        self.assertEqual(len(self.data.cache), self.num_docs)

    def test_everything_resolved(self):
        for fn, data in self.data.cache.items():
            self.assertIsInstance(data, self.data.content_class)

            self.assertNotEqual(len(data.content), 0)

            for doc in data.content.values():
                if 'source' in doc:
                    self.assertEqual(len(doc.state.keys()), self.len_source_docs)

            data.resolve()

            for doc in data.content.values():
                if 'source' in doc:
                    self.assertTrue(doc.source.resolved)


class TestBaseTemplateRendering(TestCase):
    def setUp(self):
        self.c = Configuration()
        self.c.runstate = RuntimeStateConfig()
        self.InheritableContentBase = InheritableContentBase

        self.create_data()

    def create_data(self):
        self.data = self.InheritableContentBase({}, self.c)
        self.data.replacement = {'state': 'foo'}

    def test_replacement(self):
        self.data.pre = 'this is a {{state}} test'
        self.assertTrue('{{' in self.data.pre)
        self.data.render()
        self.assertFalse('{{' in self.data.pre)
        self.assertTrue('foo' in self.data.pre)
