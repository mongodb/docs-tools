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
import os
import logging
import re
import math

import yaml
import polib

from giza.translate.utils import get_file_list

''''
This module contains functions that involve creating corpora. It has one
function that creates the appropriate train, tune, and test hybrid corpora from
smaller corpora. It has other functions that create corpora from already
translated po files as well as from multi-lingual dictionaries
'''

logger = logging.getLogger('giza.translate.corpora')


def append_corpus(percentage, num_copies, out_fn, in_fn, start, final=False):
    '''This function appends the correct amount of the corpus to the basefile,
    finishing up the file when necessary so no data goes to waste

    :param int percentage: percentage of the file going into the corpus
    :param float num_copies: number of copies of the file going into the corpus
    :param string out_fn: the name of the base file to append the corpus to
    :param string in_fn: the name of the new file to take the data from
    :param int start: the line to start copying from in the new file
    :param boolean final: if it's the final section of the file. If True it
         makes sure to use all of the way to the end of the file

    :returns: the last line it copied until
    '''
    with open(in_fn, 'r') as f:
        new_content = f.readlines()

    with open(out_fn, 'a+') as f:
        tot = int(len(new_content) * percentage / 100)
        for i in range(int(math.floor(num_copies))):
            if final is False:
                f.writelines(new_content[start:start + tot])
            else:
                f.writelines(new_content[start:])
            # if there's no new line at the end this adds one
            f.seek(-1, os.SEEK_END)
            if f.read(1) != '\n':
                f.write('\n')

        # if we have a fractional number of copies then we take care of the rest
        f.writelines(new_content[start:start + int(tot*(num_copies - math.floor(num_copies)))])

        # if there's no new line at the end this adds one
        f.seek(-1, os.SEEK_END)
        if f.read(1) != '\n':
            f.write('\n')

    return start + tot


def get_total_length(conf, corpus_type):
    '''This function finds the ideal total length of the corpus
    It finds the minimum length where each corpus section is used in full

    :param config conf: corpora configuration object
    :param string corpus_type: either train, tune, or test

    :returns: total length of the corpus
    '''
    tot_length = 0
    for file_name, source in conf.sources.items():
        if source.state['percent_of_' + corpus_type] > 0:
            temp_length = source.length*source.state['percent_' + corpus_type] / source.state['percent_of_' + corpus_type]
            if temp_length > tot_length:
                tot_length = temp_length
    return tot_length


def create_hybrid_corpora(conf):
    '''This function takes the configuration file and runs through the files,
    appending them appropriately. It first verifies that all of the percentages
    add up and then it figures out how much of each file should go into each
    corpus and appends them. The config file should be similar to corpora.yaml.
    It will copy the config file to the directory with the corpora so that you
    have a record, but the copy won't be exact. It creates both language
    corpora at the same time in parallel.

    :param config conf: corpora configuration object
    '''

    os.makedirs(conf.container_path)
    with open(os.path.join(conf.container_path, "corpora.yaml"), 'w') as f:
        yaml.dump(conf.dict(), f, default_flow_style=False)

    # append files appropriately
    for corpus_type in ('train', 'tune', 'test'):
        source_outfile = os.path.join(conf.container_path, "{0}.{1}-{2}.{1}".format(corpus_type,
                                                                                    conf.source_language,
                                                                                    conf.target_language))
        target_outfile = os.path.join(conf.container_path, "{0}.{1}-{2}.{2}".format(corpus_type,
                                                                                    conf.source_language,
                                                                                    conf.target_language))
        open(source_outfile, 'w').close()
        open(target_outfile, 'w').close()

        tot_length = get_total_length(conf, corpus_type)

        for fn, source in conf.sources.items():
            logger.info("Processing " + fn + " for " + corpus_type)

            # finds how many copies of this file will make it the correct percentage of the full corpus
            if source.state['percent_' + corpus_type] == 0 or source.state['percent_of_' + corpus_type] == 0:
                continue
            num_copies = tot_length * source.state['percent_of_' + corpus_type] / source.length / source.state['percent_' + corpus_type]
            final = False
            if corpus_type is 'test':
                final = True

            # appends the section of the file to the corpora
            end = append_corpus(source.state['percent_' + corpus_type],
                                num_copies,
                                source_outfile,
                                source.source_file_path,
                                source.end, final)
            append_corpus(source.state['percent_' + corpus_type],
                          num_copies,
                          target_outfile,
                          source.target_file_path,
                          source.end,
                          final)
            source.end = end


def write_from_po_file(source_doc, target_doc, po_file_name):
    '''This function writes two files in english and spanish from a po file's
    translated entries

    :param string source_doc: Name of file to put source lanaguge text in.
    :param string target_doc: Name of file to put target lanaguge text in.
    :param string po_file_name: Path to po file to parse
    '''
    logger.info("processing "+po_file_name)
    po = polib.pofile(po_file_name)
    for entry in po.translated_entries():
        source_doc.write(entry.msgid.encode('utf-8')+'\n')
        target_doc.write(entry.msgstr.encode('utf-8')+'\n')


def create_corpus_from_po(po_path, source_doc_fn, target_doc_fn):
    '''This function opens up the output files and then goes through the files
    in the file list and writes them all to two corpus files.

    :param string po_path: Path to po file or directory of po files
    :param string source_doc_fn: Name of file to put source lanaguge text in.
    :param string target_doc_fn: Name of file to put target lanaguge text in.
    '''

    # path is a directory now
    logger.info("walking path "+po_path)
    with open(source_doc_fn, "w", 1) as source_doc:
        with open(target_doc_fn, "w", 1) as target_doc:
            file_list = get_file_list(po_path, ["po", "pot"])
            for fn in file_list:
                write_from_po_file(source_doc, target_doc, fn)


def create_corpus_from_dictionary(dict_fn, source_fn, target_fn):
    '''This function splits a dictionary from http://www.dicts.info/uddl.php
    and turns it into a parallel corpus.

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
