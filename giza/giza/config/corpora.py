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

logger = logging.getLogger('giza.config.corpora')

from libgiza.config import ConfigurationBase

class SourceConfig(ConfigurationBase):
    _option_registry = ['name', 'source_file_path', 'target_file_path',
                        'percent_train', 'percent_tune', 'percent_test',
                        'percent_of_train', 'percent_of_tune',
                        'percent_of_test', 'length', 'end']

class CorporaConfig(ConfigurationBase):
    _option_registry = ['container_path', 'source_language', 'target_language',
                        'sources']

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
                error = "Source percentages don't add up to 100 for " + file_name
                logger.error(error)
                raise TypeError(error)

        for t in ('train', 'tune', 'test'):
            tot = 0
            for file_name,source in self.sources.items():
                tot += source.state['percent_of_' + t]
            if tot != 100:
                error = "Contribution percentages don't add up to 100 for " + t
                logger.error(error)
                raise TypeError(error)

    def get_file_lengths(self):
        '''This function adds the file lengths of the files to the configuration dictionary
        '''
        for file_name, source in self.sources.items():
            with open(source.source_file_path, 'r') as f:
                length1 = len(f.readlines())
            with open(source.target_file_path, 'r') as f:
                length2 = len(f.readlines())
            if length1 != length2:
                error = "Lengths of files for "+file_name+" are not identical"
                logger.error(error)
                raise TypeError(error)
            source.length = length1

    def dict(self):
        '''This function overrides the default dict() function to transform a corpora object into a dictionary
        '''
        # use listcomp in sources for py3 compatibility
        d = {
            'container_path': self.container_path,
            'target_language': self.target_language,
            'sources': [ s for s in self.sources.values() ]
        }

        return d

    def transform(self, input_obj):
        '''This function takes a configuration file object cand creates a dictionary of the useful information.
        It also sets defaults for certain arguments so they do not need to be specified by the user for it to work

        :param dict input_obj: original input object

        :returns: a processed dictionary of the configuration
        '''
        d = {
            'container_path' : os.path.expanduser(input_obj['container_path']),
            'source_language': input_obj['source_language'],
            'target_language': input_obj['target_language'],
            'sources': {}
        }

        # handles sources section of config
        for source in input_obj['sources']:
            for t in ('train', 'tune', 'test'):
                if source['percent_' + t] < 0 or source['percent_' + t] > 100:
                    logger.error("Invalid percentage")
                    raise TypeError("Invalid percentage")
            source['source_file_path'] = os.path.expanduser(source['source_file_path'])
            source['target_file_path'] = os.path.expanduser(source['target_file_path'])
            s = SourceConfig(source)
            s.percent_of_train = 0
            s.percent_of_tune = 0
            s.percent_of_test = 0
            s.end = 0
            d['sources'][source['name']] = s

        # handles source contributions section of config
        for t in ('train','tune','test'):
            for source in input_obj['source_contributions'][t]:
                if source['percent_of_corpus'] < 0 or source['percent_of_corpus'] > 100:
                    logger.error("Invalid percentage")
                    raise TypeError("Invalid percentage")
                d['sources'][source['name']].state['percent_of_' + t] = source['percent_of_corpus']

        return d

