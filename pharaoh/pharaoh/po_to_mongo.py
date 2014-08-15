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

import os.path
import logging
import re
import tarfile

import polib
from pymongo import MongoClient

from pharaoh.app.models import File, Sentence
from pharaoh.utils import get_file_list

'''
This module takes the po files and writes the sentences
to mongodb. This is meant to be used after translate_po.py
The file should have each entry from the given username
translated and each other entry untranslated. For every group
of po files you input them with the appropriate username and status
'''

logger = logging.getLogger('pharaoh.po_to_mongo')


def write_po_file_to_mongo(po_fn, po_file, userID, status, source_language, target_language, db):
    '''write a po_file to mongodb
    :param string po_fn: the file name of the current pofile as it should be put in mongodb
    :param POFile po_file: the polib pofile instance
    :param string userID: the ID of the user that translated the po file
    :param string status: the status of the translations
    :param string source_language: The source_language of the translations
    :param string target_language: The target_language of the translations
    :param database db: the database that you want to write to
    '''
    logger.info(po_fn)
    f = File({u'file_path': po_fn,
              u'priority': 0,
              u'source_language': source_language,
              u'target_language': target_language}, curr_db=db)

    reg = re.compile('^:[a-zA-Z0-9]+:`(?!.*<.*>.*)[^`]*`$')
    for idx, entry in enumerate(po_file):
        if entry.translated():
            sentence_status = status
            # If sentence should be autoapproved, do so
            match = re.match(reg, entry.msgstr.encode('utf-8'))
            if match is not None and match.group() == entry.msgstr.encode('utf-8'):
                sentence_status = "approved"
        else:
            sentence_status = "untranslated"

        t = Sentence({u'source_language': source_language,
                      u'source_sentence': entry.msgid.encode('utf-8'),
                      u'sentenceID': entry.tcomment.encode('utf-8'),
                      u'source_location': entry.occurrences,
                      u'sentence_num': idx,
                      u'fileID': f._id,
                      u'file_edition': f.edition,
                      u'target_sentence': entry.msgstr.encode('utf-8'),
                      u'target_language': target_language,
                      u'userID': userID,
                      u'status': sentence_status,
                      u'update_number': 0}, curr_db=db)
        t.save()
    f.get_num_sentences()

def put_po_files_in_mongo(path, username, status, source_language, target_language, db_host, db_port, db_name):
    '''go through directories and write the po file to mongo
    :param string path: the path to the po_files
    :param string username: the username of the translator
    :param string status: the status of the translations
    :param string source_language: The source_language of the translations
    :param string target_language: The target_language of the translations
    :param string db_host: the hostname of the database
    :param int db_port: the port of the database
    :param string db_name: the name of the database
    '''

    if not os.path.exists(path):
        err = path + "doesn't exist"
        logger.error(err)
        raise TypeError(err)

    db = MongoClient(db_host, db_port)[db_name]
    userID = db['users'].find_one({'username': username})[u'_id']

    logger.info("walking directory " + path)
    file_list = get_file_list(path, ["po", "pot"])
    if len(file_list) == 1:
        path = os.path.dirname(path)

    for fn in file_list:
        po = polib.pofile(fn)
        rel_fn = os.path.relpath(fn, path)
        rel_fn = os.path.splitext(rel_fn)[0]
        write_po_file_to_mongo(fn, po, userID, status, source_language,
                               target_language, db)


def put_po_data_in_mongo(po_tar, username, status, source_language, target_language, db):
    '''go through a tar of directories and write the po file to mongo
    :param string po_tar: the tar of a set of po files
    :param string username: the username of the translator
    :param string status: the status of the translations
    :param string source_language: The source_language of the translations
    :param string target_language: The target_language of the translations
    :param database db: the mongodb database
    '''

    tar = tarfile.open(fileobj=po_tar)
    for member in tar.getmembers():
        if os.path.splitext(member.name)[1] not in ['.po', '.pot']:
            continue
        po_file = tar.extractfile(member)
        po = polib.pofile(po_file.read())
        userID = db['users'].find_one({'username': username})[u'_id']
        write_po_file_to_mongo(os.path.splitext(member.name)[0], po, userID, status, source_language,
                               target_language, db)
