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

import polib
from pymongo import MongoClient

from pharaoh.utils import get_file_list

''''
This module takes the data in mongodb and writes out any approved (or all)
sentence translations to the po files. Make sure you copy the files first
to have a backup in case it messes up.
'''

logger = logging.getLogger('pharaoh.mongo_to_po')


def write_po_file(po_fn, db, is_all):
    ''' writes approved or all trnalstions to file
    :param string po_fn: the path to the current po file to write
    :param database db: mongodb database
    :param boolean is_all: whether or not you want all or just approved translations
    '''

    logger.info("writing " + po_fn)
    po = polib.pofile(po_fn)
    for entry in po.untranslated_entries():
        if is_all is False:
            t = db['translations'].find({"status": "approved", "sentenceID": entry.tcomment})
        else:
            t = db['translations'].find({"sentenceID": entry.tcomment})

        if t.count() > 1:
            logger.info("multiple approved translations with sentenceID: " + entry.tcomment)
            continue
        if t.count() == 1:
            entry.msgstr = unicode(t[0]['target_sentence'].strip())
        else:
            logger.info("multiple approved translations with sentenceID: " + entry.tcomment)


    po.save(po_fn)


def write_mongo_to_po_files(path, db_host, db_port, db_name, is_all):
    ''' goes through directory tree and writes po files to mongo
    :param string path: the path to the top level directory of the po_files
    :param string db_host: the hostname of the database
    :param int db_port: the port of the database
    :param string db_name: the name of the database
    :param boolean is_all: whether or not you want all or just approved translations
    '''

    if not os.path.exists(path):
        logger.error("{0} doesn't exist".format(path))
        return

    db = MongoClient(db_host, db_port)[db_name]

    logger.info("walking directory " + path)
    file_list = get_file_list(path, ["po", "pot"])

    for fn in file_list:
        write_po_file(fn, db, is_all)
