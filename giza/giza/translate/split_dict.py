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
import sys
import re
import logging

'''
This module is useful for taking a dictionary file from http://www.dicts.info/uddl.php and parsing it into a parallel corpus
'''

logger = logging.getLogger('giza.translate.split_dict')

def split_dict(dict_fn, source_fn, target_fn):
     '''This function splits a dictionary in half 
    :param string dict_fn: path to dictionary file  
    :param string source_fn: path to file to write source text to
    :param string target_fn: path to file to write target text to
    '''
     with open(dict_fn, "r") as dict_f:
        with open(source_fn, "w", 1) as source_f:
            with open(target_fn, "w", 1) as target_f:
                for line in dict_f:
                    if line[0] == '#':
                        continue
                    halves = re.split(r'\t+', line)
                    if len(halves) < 2:
                        continue          
                    source_words = re.split(r';', halves[0])       
                    target_words = re.split(r';', halves[1])
                    for target_word in target_words:
                        target_word = target_word.strip()
                        for source_word in source_words:
                            source_word = source_word.strip()
                            source_f.write(source_word)
                            source_f.write("\n")
                            target_f.write(target_word)
                            target_f.write("\n")
    