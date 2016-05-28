from nose.tools import nottest, istest

import os

# this runs tests of the inheritance.py baseclasses, as is.
from libgiza.test.test_inheritance import (TestDataCache, TestDataContentBase,
                                           TestInheritedContentResolution,
                                           TestBaseTemplateRendering,
                                           get_test_file_path,
                                           get_inheritance_data_files)

from giza.config.main import Configuration
from giza.config.runtime import RuntimeStateConfig

import libgiza.test
import libgiza.git

import giza.inheritance
import giza.config.git

import giza.content.steps.inheritance
import giza.content.steps.models
import giza.content.options.inheritance
import giza.content.options.models
import giza.content.tocs.inheritance
import giza.content.tocs.models
import giza.content.extract.inheritance
import giza.content.extract.models
import giza.content.release.inheritance
import giza.content.release.models
import giza.content.examples.inheritance
import giza.content.examples.models

def get_local_data_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

class TestGizaDataCache(TestDataCache):
    def setUp(self):
        self.c = Configuration()
        self.c.project = {'name': 'test'}
        self.c.runstate = RuntimeStateConfig()
        self.c.state['git'] = giza.config.git.GitConfig({}, self.c, os.getcwd())

        self.setUpClasses()
        self.create_data()

    def setUpClasses(self):
        path = get_test_file_path()
        self.c.paths = {'includes': path,
                        'source': path,
                        'projectroot': path,
                        'output': path}

        self.DataContentBase = giza.inheritance.DataContentBase
        self.DataCache = giza.inheritance.DataCache

class TestGizaDataContentBase(TestDataContentBase):
    def setUp(self):
        self.c = Configuration()
        self.c.project = {'name': 'test'}
        self.c.runstate = RuntimeStateConfig()
        self.c.state['git'] = giza.config.git.GitConfig({}, self.c, os.getcwd())

        self.setUpClasses()
        self.create_data()

    def setUpClasses(self):
        path = get_test_file_path()
        self.c.paths = {'includes': path,
                        'projectroot': path}
        self.dummy_doc = {'ref': 'dummy-doc',
                          'pre': 'pre text'}

        self.content_fn = get_inheritance_data_files()[0]
        self.DataContentBase = giza.inheritance.DataContentBase
        self.DataCache = giza.inheritance.DataCache
        self.InheritableContentBase = giza.inheritance.InheritableContentBase

class TestGizaInheritedContentResolution(TestInheritedContentResolution):
    def setUp(self):
        self.c = Configuration()
        self.c.project = {'name': 'test'}
        self.c.runstate = RuntimeStateConfig()
        self.c.state['git'] = giza.config.git.GitConfig({}, self.c, os.getcwd())

        self.setUpClasses()
        self.create_data()

    def setUpClasses(self):
        path = get_test_file_path()
        self.c.paths = {'includes': path,
                        'source': path,
                        'output': path,
                        'projectroot': path}

        self.DataCache = giza.inheritance.DataCache

class TestGizaBaseTemplateRendering(TestBaseTemplateRendering):
    def setUp(self):
        self.c = Configuration()
        self.c.runstate = RuntimeStateConfig()
        self.c.state['git'] = giza.config.git.GitConfig({}, self.c, os.getcwd())
        self.setUpClasses()
        self.create_data()

    def setUpClasses(self):
        self.InheritableContentBase = giza.inheritance.InheritableContentBase

# Base Classes for Reuse

@nottest
class GizaDataCacheBase(TestGizaDataCache):
    def create_data(self):
        path = get_local_data_path()
        self.c.paths = {'includes': path,
                        'source': path,
                        'projectroot': path,
                        'output': path}

        self.files = [os.path.join(get_local_data_path(), fn)
                      for fn in (self.short_name + '-one.yaml',
                                 self.short_name + '-two.yaml')]

        self.data = self.DataCache([], self.c)

@nottest
class GizaDataContentBase(TestGizaDataContentBase):
    def create_data(self):
        self.content_fn = os.path.join(get_local_data_path(),
                                       self.short_name + '-one.yaml')

        self.data = self.DataCache([self.content_fn], self.c)
        self.content = self.data.cache[self.content_fn]

@nottest
class GizaInheritedContentResolutionBase(TestGizaInheritedContentResolution):
    def create_data(self):
        path = get_local_data_path()
        self.c.paths = {'includes': path,
                        'source': path,
                        'projectroot': path,
                        'output': path}

        self.files = [os.path.join(self.c.paths.source, fn)
                      for fn in (self.short_name + '-one.yaml',
                                 self.short_name + '-two.yaml')]

        self.data = self.DataCache(self.files, self.c)


# Pass-through Tests of Steps

@istest
class TestStepsDataCache(GizaDataCacheBase):
    def setUpClasses(self):
        self.DataContentBase = giza.content.steps.inheritance.StepFile
        self.DataCache = giza.content.steps.inheritance.StepDataCache
        self.short_name = 'steps'


@istest
class TestStepsDataContentBase(GizaDataContentBase):
    def setUpClasses(self):
        self.DataContentBase = giza.content.steps.inheritance.StepFile
        self.DataCache = giza.content.steps.inheritance.StepDataCache
        self.InheritableContentBase = giza.content.steps.models.StepData
        self.short_name = 'steps'

        self.dummy_doc = {'ref': 'dummy-doc',
                          'pre': 'pre text'}


@istest
class TestStepsInheritedContentResolution():
    def setUpClasses(self):
        self.DataCache = giza.content.steps.inheritance.StepDataCache
        self.short_name = 'steps'
        self.len_source_docs = 9
        self.num_docs = 2

# Pass-through Tests of Options

@istest
class TestOptionsDataCache(GizaDataCacheBase):
    def setUpClasses(self):
        self.DataContentBase = giza.content.options.inheritance.OptionFile
        self.DataCache = giza.content.options.inheritance.OptionDataCache
        self.short_name = 'options'


@istest
class TestOptionsDataContentBase(GizaDataContentBase):
    def setUpClasses(self):
        self.DataContentBase = giza.content.options.inheritance.OptionFile
        self.DataCache = giza.content.options.inheritance.OptionDataCache
        self.InheritableContentBase = giza.content.options.models.OptionData
        self.short_name = 'options'

        self.dummy_doc = {'name': 'dummydoc',
                          'program': 'test',
                          'pre': 'pre text'}

@istest
class TestOptionsInheritedContentResolution(GizaInheritedContentResolutionBase):
    def setUpClasses(self):
        self.DataCache = giza.content.options.inheritance.OptionDataCache
        self.short_name = 'options'
        self.len_source_docs = 9
        self.num_docs = 2

# Pass-through Tests of Tocs

@istest
class TestTocsDataCache(GizaDataCacheBase):
    def setUpClasses(self):
        self.DataContentBase = giza.content.tocs.inheritance.TocFile
        self.DataCache = giza.content.tocs.inheritance.TocDataCache
        self.short_name = 'toc'

@istest
class TestTocsDataContentBase(GizaDataContentBase):
    def setUpClasses(self):
        self.DataContentBase = giza.content.tocs.inheritance.TocFile
        self.DataCache = giza.content.tocs.inheritance.TocDataCache
        self.InheritableContentBase = giza.content.tocs.models.TocData
        self.short_name = 'toc'

        self.dummy_doc = {'name': 'dummydoc',
                          'file': '/path/to/doc',
                          'description': 'text'}

@istest
class TestTocsInheritedContentResolution(GizaInheritedContentResolutionBase):
    def setUpClasses(self):
        self.DataCache = giza.content.tocs.inheritance.TocDataCache
        self.short_name = 'toc'
        self.len_source_docs = 7
        self.num_docs = 2


# Pass-through Tests of Extracts

@istest
class TestExtractsDataCache(GizaDataCacheBase):
    def setUpClasses(self):
        self.DataContentBase = giza.content.extract.inheritance.ExtractFile
        self.DataCache = giza.content.extract.inheritance.ExtractDataCache
        self.short_name = 'extracts'



@istest
class TestExtractsDataContentBase(GizaDataContentBase):
    def setUpClasses(self):
        self.DataContentBase = giza.content.extract.inheritance.ExtractFile
        self.DataCache = giza.content.extract.inheritance.ExtractDataCache
        self.InheritableContentBase = giza.content.extract.models.ExtractData
        self.short_name = 'extracts'

        self.dummy_doc = {'ref': 'dummy-doc',
                          'pre': 'pre text'}


@istest
class TestExtractsInheritedContentResolution(GizaInheritedContentResolutionBase):
    def setUpClasses(self):
        self.DataCache = giza.content.extract.inheritance.ExtractDataCache
        self.short_name = 'extracts'
        self.len_source_docs = 4
        self.num_docs = 2


# Pass-through Tests of Releases

@istest
class TestReleasesDataCache(GizaDataCacheBase):
    def setUpClasses(self):
        self.DataContentBase = giza.content.release.inheritance.ReleaseFile
        self.DataCache = giza.content.release.inheritance.ReleaseDataCache
        self.short_name = 'release'


@istest
class TestReleasesDataContentBase(GizaDataContentBase):
    def setUpClasses(self):
        self.DataContentBase = giza.content.release.inheritance.ReleaseFile
        self.DataCache = giza.content.release.inheritance.ReleaseDataCache
        self.InheritableContentBase = giza.content.release.models.ReleaseData
        self.short_name = 'release'

        self.dummy_doc = {'ref': 'dummy-doc',
                          'pre': 'pre text'}


@istest
class TestReleasesInheritedContentResolution(GizaInheritedContentResolutionBase):
    def setUpClasses(self):
        self.DataCache = giza.content.release.inheritance.ReleaseDataCache
        self.short_name = 'release'
        self.len_source_docs = 5
        self.num_docs = 2


# Pass-through Tests of Examples

@istest
class TestExamplesDataCache(GizaDataCacheBase):
    def setUpClasses(self):
        self.DataContentBase = giza.content.examples.inheritance.ExampleFile
        self.DataCache = giza.content.examples.inheritance.ExampleDataCache
        self.short_name = 'examples'


@istest
class TestExamplesDataContentBase(GizaDataContentBase):
    def setUpClasses(self):
        self.DataContentBase = giza.content.examples.inheritance.ExampleFile
        self.DataCache = giza.content.examples.inheritance.ExampleDataCache
        self.InheritableContentBase = giza.content.examples.models.ExampleData
        self.short_name = 'examples'

        self.dummy_doc = {'ref': 'dummy-doc',
                          'pre': 'pre text',
                          'operation': { 'language': 'javascript',
                                         'code': ['use db']}}


@istest
class TestExamplesInheritedContentResolution(GizaInheritedContentResolutionBase):
    def setUpClasses(self):
        self.DataCache = giza.content.examples.inheritance.ExampleDataCache
        self.short_name = 'examples'
        self.len_source_docs = 9
        self.num_docs = 2
