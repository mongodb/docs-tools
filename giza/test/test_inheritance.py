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

from giza.inheritance import DataContentBase, DataCache, InheritableContentError, InheritableContentBase

from giza.config.main import Configuration
from giza.config.runtime import RuntimeStateConfig
from giza.config.base import RecursiveConfigurationBase

class DummyRecord(InheritableContentBase):
    _option_registry = ['pre', 'post', 'ref', 'title', 'edition', 'operation', 'results']
class DummyContent(DataContentBase):
    content_class = DummyRecord
class DummyCache(DataCache):
    content_class = DummyContent


def get_inheritance_data_files():
    return [
        os.path.abspath(os.path.join(os.path.dirname(__file__), 'data-inheritance', fn))
        for fn in ( 'example-add-one.yaml', 'example-add-two.yaml',
                    'example-add-three.yaml' )
    ]

class TestDataCache(TestCase):
    @classmethod
    def setUp(self):
        self.c = Configuration()
        self.c.runstate = RuntimeStateConfig()
        self.c.paths = { 'includes':
                         os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data-inheritance')}

        self.data = DummyCache([], self.c)

    def test_content_class_default(self):
        self.assertEqual(self.data.cache, {})
        self.assertIs(self.data.content_class, DummyContent)

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
        files = get_inheritance_data_files()
        self.assertEqual(self.data.cache, {})
        self.data.ingest(files)
        self.assertNotEqual(self.data.cache, {})

        for fn in files:
            self.assertIn(fn, self.data)

    def test_ingest_ignore_duplicates(self):
        files = get_inheritance_data_files()
        self.assertEqual(self.data.cache, {})
        self.data.ingest(files)
        self.data.ingest(files)
        self.assertNotEqual(self.data.cache, {})

        self.assertEqual(len(self.data.cache), len(files))

    def test_add_file(self):
        self.assertEqual(self.data.cache, {})
        for fn in get_inheritance_data_files():
            self.data.add_file(fn)
            self.assertIn(fn, self.data.cache)
            self.assertIn(fn, self.data)
            self.assertIsInstance(self.data.cache[fn], self.data.content_class)

    def test_fetch(self):
        files = get_inheritance_data_files()
        self.assertEqual(self.data.cache, {})
        self.data.ingest(files)

        for fn in files:
            self.assertIn(fn, self.data)
            for idx in range(len(self.data.cache), 1):
                content = self.data.fetch(fn, idx)
                self.assertIsInstance(content, dict)

        self.assertEqual(len(self.data.cache), len(files))

    def test_fetch_without_adding_file(self):
        files = get_inheritance_data_files()
        self.assertEqual(self.data.cache, {})

        for fn in files:
            with self.assertRaises(InheritableContentError):
                content = self.data.fetch(fn, 1)

            self.assertNotIn(fn, self.data)

class TestDataContentBase(TestCase):
    @classmethod
    def setUp(self):
        self.c = Configuration()
        self.c.runstate = RuntimeStateConfig()
        self.c.paths = { 'includes':
                         os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data-inheritance')}

        self.content_fn = get_inheritance_data_files()[0]

        self.data = DummyCache([], self.c)
        self.data.ingest([self.content_fn])

        self.content = self.data.cache[self.content_fn]

    def test_content_created(self):
        for fn, example in self.data.cache.items():
            for v in example.content.values():
                self.assertIsInstance(v, RecursiveConfigurationBase)

    def test_content_is_correct_type(self):
        self.assertIsInstance(self.content, DataContentBase)

    def test_content_state_reference(self):
        self.assertIs(self.content.content, self.content.state['content'])

    def test_reference_to_cache(self):
        self.assertIs(self.content.data, self.data)

    def test_fetching_content(self):
        for idx in self.content.content:
            self.assertIs(self.content.content[idx], self.data.fetch(self.content_fn, idx))

    def test_resolve_checker(self):
        if isinstance(self.content, dict):
            with self.assertRaises(AttributeError):
                self.content.is_resolved()
        else:
            self.assertIsInstance(self.content.is_resolved(), bool)

class TestInheritedContentResolution(TestCase):
    @classmethod
    def setUp(self):
        self.c = Configuration()
        self.c.runstate = RuntimeStateConfig()
        self.c.paths = { 'includes':
                         os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data-inheritance')}

        self.data = DummyCache(get_inheritance_data_files(), self.c)

    def test_gross_correctness_of_ingestion(self):
        self.assertEqual(len(self.data.cache), 3)

    def test_everything_resolved(self):
        for fn, data in self.data.cache.items():
            self.assertIsInstance(data, self.data.content_class)

            self.assertNotEqual(len(data.content), 0)

            for doc in data.content.values():
                if 'source' in doc:
                    self.assertFalse(doc.source.resolved)

            data.resolve()

            for doc in data.content.values():
                if 'source' in doc:
                    self.assertTrue(doc.source.resolved)
