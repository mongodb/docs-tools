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
import shutil
import os
import re

import polib

from giza.translate.utils import TempDir, get_file_list, flip_text_direction
from giza.tools.command import command

'''
This module has functions for translating files. It has a function for
translating any file given a config and it has a functioni for translating
a directory of po files. The po file translator takes the directory,
writes the source language to a file, then translates that to another
file, and then writes that out in the same order as it ingested the
directory. It translates the untranslated entries and empties the
translated ones to isolate the machine translated ones.Thus it is
important not to change the directory structure mid running this program.
MAKE SURE TO COPY THE DIRECTORY OF PO FILES BEFORE TRANSLATING THEM,
anything that was already translated will be deleted by this, this is
intentional. The goal of this module is to make a directory tree with
translations ONLY by Moses, because then those translations can be looked
at separately from approved or human translated sentences.
'''

logger = logging.getLogger('giza.translate.translation')


def translate_file(in_file, out_file,  tconf, protected_file, super_temp=None):
    '''This function translates a given file to another language

    :param string in_file: path to file to be translated
    :param string out_file: path to file where translated output should be written
    :param config tconf: translateconfig object
    :param string protected_file': path to regex file to protect expressions from tokenization
    :param string super_temp: If you have a TempDir context inside of a TempDir
       context, this allows you to not create two. Just pass in the directory of
       the previous temporary directory
    '''

    if out_file is None:
        out_file = in_file + ".translated"

    with TempDir(super_temp=super_temp) as temp:
        logger.info("tempdir: " + temp)
        logger.info("decoding: " + in_file)
        if os.stat(in_file).st_size == 0:
            logger.warning("File is empty")
            open(out_file, "w").close()
            return
        if super_temp is None:
            shutil.copy(in_file, temp)
        in_file = os.path.basename(in_file)

        if protected_file is not None:
            command("{0}/scripts/tokenizer/tokenizer.perl -l en < {4}/{1} > {4}/{1}.tok.en -threads {2} -protected {3}".format(tconf.paths.moses, in_file, tconf.settings.threads, protected_file, temp), logger=logger, capture=True)
        else:
            command("{0}/scripts/tokenizer/tokenizer.perl -l en < {3}/{1} > {3}/{1}.tok.en -threads {2}".format(tconf.paths.moses, in_file, tconf.settings.threads, temp), logger=logger, capture=True)

        command("{0}/scripts/recaser/truecase.perl --model {1}/truecase-model.en < {3}/{2}.tok.en > {3}/{2}.true.en".format(tconf.paths.moses, tconf.paths.aux_corpus_files, in_file, temp), logger=logger, capture=True)
        command("{0}/bin/moses -f {1}/{3}/working/binarised-model/moses.ini < {4}/{2}.true.en > {4}/{2}.true.trans".format(tconf.paths.moses, tconf.paths.project, in_file, tconf.settings.best_run, temp), logger=logger, capture=True)
        command("{0}/scripts/recaser/detruecase.perl < {2}/{1}.true.trans > {2}/{1}.tok.trans".format(tconf.paths.moses, in_file, temp), logger=logger, capture=True)
        command("{0}/scripts/tokenizer/detokenizer.perl -l en < {3}/{1}.tok.trans > {2}".format(tconf.paths.moses, in_file, out_file, temp), logger=logger, capture=True)


def po_file_untranslated_to_text(text_doc, po_file):
    '''This function writes a po file out to a text file

    :param string text_doc: the path to the text document to write the po file sentences to
    :param string po_file: the path to the po_file to write from
    '''
    logger.info("writing out from " + po_file)
    po = polib.pofile(po_file)

    for entry in po.untranslated_entries():
        text_doc.write(entry.msgid.encode('utf-8') + '\n')


def extract_all_untranslated_po_entries(po_file_list, temp_dir):
    '''This function extracts all of the untranslated entries in
    the directory structure

    :param list po_file_list: the list of po files
    :param string temp_dir: the path to the temporary directory

    :returns: the path to the temporary source file
    '''

    with open(temp_dir+"/source", "w") as temp:
        for fn in po_file_list:
            po_file_untranslated_to_text(temp, fn)

    return temp_dir + "/source"


def fill_po_file(target_po_file, translated_lines, start):
    '''This function fills a new po file with the translated lines
    :param string target_po_file: the path to the current po file
    :param list translated_lines: the list of translated lines
    :param int start: the line to start at when writing out this file
    :returns: The start of the sentences for the next file
    '''
    logger.info("writing out to " + target_po_file)
    po = polib.pofile(target_po_file)
    i = -1
    for entry in po:
        if entry.translated() is False:
            i += 1
            entry.msgstr = unicode(translated_lines[start+i].strip(), "utf-8")
        else:
            entry.msgstr = ""

    po.save(target_po_file)
    return start + i + 1


def write_po_files(po_file_list, translated_temp):
    ''' This function writes all of the lines to their po files
    :param list po_file_list: the list of translated lines
    :param string translated_temp: the temproray translated file
    '''
    start = 0
    with open(translated_temp, "r") as trans:
        trans_lines = trans.readlines()

    for fn in po_file_list:
        start = fill_po_file(fn, trans_lines, start)


def translate_po_files(po_path, tconf, protected_file=None):
    ''' This function translates a directory of po files in three steps:
    First it extracts the untranslated entries from every po file into one
    big file. Then it translates that file. Lastly it fills in all of the
    po files in the same order the entries were extracted, removing the text
    from any translated entries.
    :param string po_path: the path to the top level directory of the po_files
    :param config tconf: translation config object
    :param string protected_file: path to file with regexes to protect
    '''

    with TempDir() as temp_dir:
        po_file_list = get_file_list(po_path, ["po", "pot"])
        temp_file = extract_all_untranslated_po_entries(po_file_list, temp_dir)
        trans_file = temp_file + '.translated'
        translate_file(temp_file, trans_file, tconf, protected_file, temp_dir)

        # flips the file if the language is right to left
        if tconf.settings.foreign in ['he', 'ar']:
            flipped_file = trans_file + '.flip'
            flip_text_direction(trans_file, flipped_file)
            trans_file = flipped_file

        write_po_files(po_file_list, trans_file)


def auto_approve_po_entries(po_path):
    ''' This function automatically approves any untranslated sentence in a
    po file that should be identical in the target language. These sentences
    are of the form ``:word:\`link\```
    :param string po_path: the path to the top level directory of the po_files
    '''
    po_file_list = get_file_list(po_path, ["po", "pot"])
    reg = re.compile('^:[a-zA-Z0-9]+:`(?!.*<.*>.*)[^`]*`$')
    for fn in po_file_list:
        po = polib.pofile(fn)
        for entry in po.untranslated_entries():
            match = re.match(reg, entry.msgid.encode('utf-8'))
            if match is not None and match.group() == entry.msgid.encode('utf-8'):
                entry.msgstr = entry.msgid
        po.save()
