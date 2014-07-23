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
from giza.translate.translate_doc import decode, TempDir
from giza.files import expand_tree
import logging

'''
This module translates a directory of po files
It takes the directory, writes the source language to a file, then translates that to another file, and then writes that out in the same order as it ingested the directory
It translates the untranslated entries and empties the translated ones to isolate the machine translated ones
Thus it is important not to change the directory structure mid running this program
MAKE SURE TO COPY THE DIRECTORY OF PO FILES BEFORE TRANSLATING THEM, anything that was already translated will be deleted by this, this is intentional
The goal of this module is to make a directory tree with translations ONLY by Moses.
Then those translations can be looked at separately from approved or human translated sentences
'''

logger = logging.getLogger('translate_po')

def write_text_file(text_doc, po_file):
    '''This function writes a po file out to a text file
    :param string text_doc: the path to the text document to write the po file sentences to
    :param string po_file: the path to the po_file to write from
    '''
    logger.info("processing {0}".format(po_file))
    po = polib.pofile(po_file)
    for entry in po.untranslated_entries():
        text_doc.write(entry.msgid.encode('utf-8')+'\n')

def extract_untranslated_entries(po_file_list, temp_dir):
    '''This function extracts all of the untranslated entries in the directory structure
    :param list po_file_list: the list of po files
    :param string temp_dir: the path to the temporary directory
    :returns: the path to the temporary source file
    '''

    #extract entries into temp
    with open(temp_dir+"/source", "w") as temp:
        for fn in po_file_list:
            write_text_file(temp, fn)
    return temp_dir+"/source"


def fill_target(target_po_file, translated_lines, start):
    '''This function fills a new po file with the translated lines
    :param string target_po_file: the path to the current po file
    :param list translated_lines: the list of translated lines
    :param int start: the line to start at when writing out this file
    :returns: The start of the sentences for the next file
    '''
    po = polib.pofile(target_po_file)
    i = -1
    for entry in po:
        if entry.translated() is False:
            i += 1
            entry.msgstr = unicode(translated_lines[start+i].strip(), "utf-8")
        else:
            entry.msgstr = ""

    # Save translated po file.
    po.save(target_po_file)
    return start + i + 1

def write_to_po(po_file_list, translated_temp):
    ''' This function writes all of the lines to their po files
    :param list po_file_list: the list of translated lines 
    :param string translated_temp: the temproray translated file
    '''
    start = 0
    with open(translated_temp, "r") as trans:
        trans_lines = trans.readlines()

    for fn in po_file_list:
        start = fill_target(fn, trans_lines, start)

def get_file_list(path, input_extension):
    ''' This function wraps around expand tree to return a list of only 1 file 
    if the user gives a path to a file and not a directory
    :param string path: path to the file
    :param list input_extension: a list (or a single) of extensions that is acceptable
    '''
    if os.path.isfile(path):
        if input_extension != None:
            if isinstance(input_extension, list):
                if os.path.splitext(path)[1][1:] not in input_extension:
                    return []
            else:
                if not path.endswith(input_extension):
                    return []
        return [path]
    return expand_tree(path, input_extension)


def translate_po_files(po_path, tconf, protected_file=None):
    ''' This function first extracts the entries, then translates them, and then fills in all of the files
    :param string po_path: the path to the top level directory of the po_files
    :param config tconf: translation config object
    :param string protected_file: path to file with regexes to protect
    '''
    with TempDir() as temp_dir:
        po_file_list = get_file_list(po_path, ["po", "pot"])
        logger.info(po_file_list)
        # extract untranslated entries to temp_file
        temp_file = extract_untranslated_entries(po_file_list, temp_dir)
        # translate temp_file
        decode(temp_file, temp_file+'.translated', tconf, protected_file, temp_dir)
        # put temp_file back in po files
        write_to_po(po_file_list, temp_file+'.translated')
        

