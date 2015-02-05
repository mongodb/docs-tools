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
import os

from libgiza.config import ConfigurationBase, RecursiveConfigurationBase
logger = logging.getLogger('giza.config.translate')


class TranslateConfig(RecursiveConfigurationBase):

    def __init__(self, input_obj, conf):
        if isinstance(input_obj, list):
            logger.error("Config doesn't exist")
            raise TypeError
        else:
            super(TranslateConfig, self).__init__(input_obj, conf)

    @property
    def settings(self):
        return self.state['settings']

    @settings.setter
    def settings(self, value):
        self.state['settings'] = SettingsConfig(value)

    @property
    def train(self):
        return self.state['train']

    @train.setter
    def train(self, value):
        self.state['train'] = CorpusTypeConfig(value)

    @property
    def tune(self):
        return self.state['tune']

    @tune.setter
    def tune(self, value):
        self.state['tune'] = CorpusTypeConfig(value)

    @property
    def test(self):
        return self.state['test']

    @test.setter
    def test(self, value):
        self.state['test'] = CorpusTypeConfig(value)

    @property
    def training_parameters(self):
        return self.state['training_parameters']

    @training_parameters.setter
    def training_parameters(self, value):
        self.state['training_parameters'] = TrainingParametersConfig(value)

    @property
    def paths(self):
        return self.state['paths']

    @paths.setter
    def paths(self, value):
        self.state['paths'] = PathsConfig(value)


class SettingsConfig(ConfigurationBase):
    _option_registry = ['foreign', 'threads', 'pool_size', 'email',
                        'phrase_table_name', 'reordering_name', 'best_run']


class PathsConfig(ConfigurationBase):

    @property
    def moses(self):
        return self.state['moses']

    @moses.setter
    def moses(self, value):
        self.state['moses'] = os.path.expanduser(value)
        if os.path.exists(self.state['moses']) is False:
            raise TypeError(value + ' does not exist')

    @property
    def irstlm(self):
        return self.state['irstlm']

    @irstlm.setter
    def irstlm(self, value):
        self.state['irstlm'] = os.path.expanduser(value)
        if os.path.exists(self.state['irstlm']) is False:
            raise TypeError(value + ' does not exist')

    @property
    def aux_corpus_files(self):
        return self.state['aux_corpus_files']

    @aux_corpus_files.setter
    def aux_corpus_files(self, value):
        self.state['aux_corpus_files'] = os.path.expanduser(value)
        if os.path.exists(self.state['aux_corpus_files']) is False:
            raise TypeError(value + ' does not exist')

    @property
    def project(self):
        return self.state['project']

    @project.setter
    def project(self, value):
        self.state['project'] = os.path.expanduser(value)
        if os.path.exists(self.state['project']) is False:
            raise TypeError(value + ' project')


class CorpusTypeConfig(ConfigurationBase):
    _option_registry = ['name']

    @property
    def dir(self):
        return self.state['dir']

    @dir.setter
    def dir(self, value):
        self.state['dir'] = os.path.expanduser(value)
        if os.path.exists(self.state['dir']) is False:
            raise TypeError(value + ' does not exist')


class TrainingParametersConfig(ConfigurationBase):
    _option_registry = ['alignment', 'max_phrase_length', 'order',
                        'reordering_directionality', 'reordering_language', 'reordering_modeltype',
                        'reordering_orientation', 'score_options', 'smoothing']

    def __init__(self, input_obj):
        input_obj = self.transform(input_obj)
        super(TrainingParametersConfig, self).__init__(input_obj)

    def transform(self, input_obj):
        for k, param in input_obj.items():
            if isinstance(param, list) is False:
                input_obj[k] = [param]
        return input_obj
