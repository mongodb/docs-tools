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

from __future__ import division
import sys
import os
import yaml
import logging
import giza.config.corpora
''''
This module creates the appropriate train, tune, and test corpora
It takes a config file similar to corpora.yaml
'''

logger = logging.getLogger('giza.translate.create_corpora')


def append_corpus(percentage, num_copies, out_fn, in_fn, start, final=False):
    '''This function appends the correct amount of the corpus to the basefile, finishing up the file when necessary so no data goes to waste
    :param int percentage: percentage of the file going into the corpus 
    :param float num_copies: number of copies of the file going into the corpus 
    :param string out_fn: the name of the base file to append the corpus to 
    :param string in_fn: the name of the new file to take the data from 
    :param int start: the line to start copying from in the new file 
    :param boolean final: if it's the final section of the file. If True it makes sure to use all of the way to the end of the file
    :returns: the last line it copied until
    '''
    with open(in_fn, 'r') as f:
        new_content = f.readlines()
    
    with open(out_fn, 'a') as f:
        tot = int(len(new_content) * percentage / 100)
        i = 1
        while i <= num_copies:
            if final is False:
                f.writelines(new_content[start:start+tot])
            else:
                f.writelines(new_content[start:])
            i += 1   
        if i!=num_copies: 
            f.writelines(new_content[start:start+int(tot*(num_copies-i+1))])
            
    return start + tot

def get_total_length(conf, corpus_type):
    '''This function finds the ideal total length of the corpus
    It finds the minimum length where each corpus section is used in full
    :param config conf: corpora configuration object
    :param string corpus_type: either train, tune, or test
    :returns: total length of the corpus
    '''
    tot_length=0
    i=0
    for file_name, source in conf.sources.items():
        if source.state['percent_of_'+corpus_type] > 0 and source.length * 100 / source.state['percent_of_'+corpus_type] > tot_length:
            tot_length = source.length * 100 / source.state['percent_of_'+corpus_type]
        i += 1
    return tot_length
 

def run_corpora_creation(conf):
    '''This function takes the configuration file and runs through the files, appending them appropriately
    It first verifies that all of the percentages add up and then it figures out how much of each file should go into each corpus and appends them
    :param config conf: corpora configuration object
    '''
    
    if os.path.exists(conf.container_path) is False:
        os.makedirs(conf.container_path)
     
    #append files appropriately
    for corpus_type in ('train', 'tune', 'test'):
        source_outfile = "{0}/{1}.{2}-{3}.{2}".format(conf.container_path, corpus_type, conf.source_language ,conf.target_language)
        target_outfile = "{0}/{1}.{2}-{3}.{3}".format(conf.container_path, corpus_type, conf.source_language ,conf.target_language)
        open(source_outfile,'w').close()
        open(target_outfile,'w').close()
        # finds the total length of the entire corpus
        tot_length = get_total_length(conf, corpus_type)   
        i = 0
        for fn,source in conf.sources.items():
            logger.info("Processing "+fn+" for "+corpus_type)
            #finds how many copies of this file will make it the correct percentage of the full corpus
            num_copies = tot_length * source.state['percent_of_'+corpus_type] / 100 / source.length
            final = False
            if corpus_type is 'test': 
                final = True
            #appends the section of the file to the corpus
            end = append_corpus(source.state['percent_'+corpus_type], num_copies, source_outfile, source.source_file_path, source.end, final)
            append_corpus(source.state['percent_'+corpus_type], num_copies, target_outfile, source.target_file_path, source.end, final)
            source.end = end
            i += 1
             