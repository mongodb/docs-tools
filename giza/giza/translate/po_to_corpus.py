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

import polib
import sys
import os.path
import logging
from giza.translate.translate_po import get_file_list
'''
This module takes a po file or a directory of po files and writes it/them to a parallel corpus
It's useful for taking the po files and using them for training data for build_model
'''
logger = logging.getLogger('giza.translate.po_to_corpus')

def parse_po_file(source_doc, target_doc, po_file_name):
    '''This function writes two files in english and spanish from a po file's translated entries
    :param string source_doc: Name of file to put source lanaguge text in.
    :param string target_doc: Name of file to put target lanaguge text in.
    :param string po_file_name: Path to po file to parse
    '''
    logger.info("processing "+po_file_name)
    po = polib.pofile(po_file_name)
    for entry in po.translated_entries():
        source_doc.write(entry.msgid.encode('utf-8')+'\n')
        target_doc.write(entry.msgstr.encode('utf-8')+'\n')

def extract_translated_entries(po_path, source_doc_fn, target_doc_fn):
    '''This function opens up the output files and then goes through the files in the file list and writes them all
    :param string po_path: Path to po file or directory of po files
    :param string source_doc: Name of file to put source lanaguge text in.
    :param string target_doc: Name of file to put target lanaguge text in.
    '''
    # path is a directory now
    logger.info("walking path "+po_path)
    with open(source_doc_fn, "w", 1) as source_doc:
        with open(target_doc_fn, "w", 1) as target_doc:
            file_list = get_file_list(po_path, ["po", "pot"])
            for fn in file_list:
                parse_po_file(source_doc, target_doc, fn)
