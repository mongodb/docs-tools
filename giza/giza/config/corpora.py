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

logger = logging.getLogger('giza.config.corpora')

from giza.config.base import ConfigurationBase

class SourceConfig(ConfigurationBase):
    _option_registry = ['file_name', 'file_path', 'percent_train', 'percent_tune', 'percent_test', 'percent_of_train', 'percent_of_tune', 'percent_of_test', 'length', 'end']

    def __init__(self, input_obj):
        super(SourceConfig, self).__init__(input_obj)


class CorporaConfig(ConfigurationBase):
    _option_registry = ['name', 'foreign_language', 'corpus_language', 'sources']

    def __init__(self, input_obj):
        input_obj = self.transform(input_obj)
        super(CorporaConfig, self).__init__(input_obj)
        self.verify_percentages()
        self.get_file_lengths()

    def verify_percentages(self):
        '''This function verifies that the percentages are valid and add up to 100
        '''
        for file_name, source in self.sources.items():
            if source.percent_train + source.percent_tune + source.percent_test != 100:
                 logger.error("Source percentages don't add up to 100 for "+file_name)
                 raise TypeError("Source percentages don't add up to 100 for "+file_name)

        for t in ('train', 'tune', 'test'):
            tot = 0
            for file_name,source in self.sources.items():
                tot += source.state['percent_of_'+t]
            if tot != 100:
                logger.error("Contribution percentages don't add up to 100 for "+t)
                raise TypeError("Contribution percentages don't add up to 100 for "+t)

    def get_file_lengths(self):
        '''This function adds the file lengths of the files to the configuration dictionary
        '''
        for file_name,source in self.sources.items():
            with open(source.file_path, 'r') as file:
                source.length = len(file.readlines())

    def transform(self, input_obj):
        '''This function takes a configuration file object cand creates a dictionary of the useful information.
        It also sets defaults for certain arguments so they do not need to be specified by the user for it to work
        :Parameters:
            - 'input_obj': original input object
        :Returns:
            - a dictionary of the configuration
        '''
        d = dict()
        d['name'] = input_obj['name']
        d['foreign_language'] = input_obj['foreign_language']
        d['corpus_language'] = input_obj['corpus_language']
        d['sources'] = dict()

        #handles sources section of config
        for source in input_obj['sources']:
            for t in ('train', 'tune', 'test'):
                if source['percent_'+t] < 0 or source['percent_'+t] > 100:
                    logger.error("Invalid percentage")
                    raise TypeError("Invalid percentage")
            s = SourceConfig(source)
            s.percent_of_train = 0
            s.percent_of_tune = 0
            s.percent_of_test = 0
            s.end = 0
            d['sources'][source['file_name']] = s

        #handles source contributions section of config
        for t in ('train','tune','test'):
            for source in input_obj['source_contributions'][t]:
                if source['percent_of_corpus'] < 0 or source['percent_of_corpus'] > 100:
                    logger.error("Invalid percentage")
                    raise TypeError("Invalid percentage")
                d['sources'][source['file_name']].state['percent_of_'+t] = source['percent_of_corpus']
        return d
            
