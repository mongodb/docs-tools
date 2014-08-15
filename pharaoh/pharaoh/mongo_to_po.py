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

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import logging
import datetime
import cStringIO
import tarfile

import polib
from pymongo import MongoClient

from pharaoh.utils import get_file_list
from pharaoh.app.models import find_file

''''
This module takes the data in mongodb and writes out any approved (or all)
sentence translations to the po files. Make sure you copy the files first
to have a backup in case it messes up.
'''

logger = logging.getLogger('pharaoh.mongo_to_po')


def write_po_file(po_fn, top_path, source_language, target_language, db, is_all):
    ''' writes approved or all trnalstions to file
    :param string po_fn: the path to the current po file to write
    :param string source_language: language to translate from
    :param string target_language: language to translate to
    :param database db: mongodb database
    :param boolean is_all: whether or not you want all or just approved translations
    '''

    logger.info("writing " + po_fn)
    po = polib.pofile(po_fn)
    rel_fn = os.path.relpath(po_fn, top_path)
    rel_fn = os.path.splitext(rel_fn)[0]
    file_record = find_file(source_language, target_language, rel_fn, curr_db=db)
    for entry in po.untranslated_entries():
        if is_all is False:
            t = db['translations'].find({"status": "approved", "sentenceID": entry.tcomment, "source_language": source_language, "target_language": target_language, 'file_edition': file_record['edition']})
        else:
            t = db['translations'].find({"sentenceID": entry.tcomment, "source_language": source_language, "target_language": target_language, 'file_edition': file_record['edition']})

        if t.count() == 1:
            entry.msgstr = unicode(t[0]['target_sentence'].strip())
        elif t.count() > 1:
            logger.info("multiple translations with sentenceID: " + entry.tcomment)
        else:
            logger.info("no translation for: " + entry.tcomment)


    po.save(po_fn)


def write_mongo_to_po_files(path, source_language, target_language, db_host, db_port, db_name, is_all):
    ''' goes through directory tree and writes po files to mongo
    :param string path: the path to the top level directory of the po_files
    :param string source_language: language to translate from
    :param string target_language: language to translate to
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
        write_po_file(fn, path, source_language, target_language, db, is_all)

def generate_fresh_po_text(po_fn, source_language, target_language, db, is_all):
    ''' goes through all of the sentences in a po file in the database and writes them out to a fresh po file
    :param string po fn: the path to a given po file as it would be found in the database
    :param string source_language: language to translate from
    :param string target_language: language to translate to
    :param database db: the instance of the database
    :param boolean is_all: whether or not you want all or just approved translations
    '''
    po = polib.POFile()
    po.metadata = {
        u'Project-Id-Version': 'uMongoDB Manual',
        u'Report-Msgid-Bugs-To': u'',
        u'POT-Creation-Date': unicode(str(datetime.datetime.now())),
        u'PO-Revision-Date': unicode(str(datetime.datetime.now())),
        u'Last-Translator': u'',
        u'Language-Team': unicode(target_language),
        u'MIME-Version': u'1.0',
        u'Content-Type': u'text/plain; charset=utf-8',
        u'Language': u'es',
        u'Content-Transfer-Encoding': u'8bit',
        u'Plural-Forms': u'nplurals=2; plural=(n != 1);'
    }
    file_record = find_file(source_language, target_language, po_fn, curr_db=db)
    if file_record is not None:
        sentences = db['translations'].find({'fileID': file_record[u'_id'],
                                             'file_edition': file_record[u'edition']},
                                            {'_id': 1,
                                             'source_sentence': 1,
                                             'target_sentence': 1,
                                             'source_location': 1,
                                             'sentenceID': 1,
                                             'status': 1} ).sort('sentence_num', 1)
        for sentence in sentences:
            translation = sentence['target_sentence'].strip()
            if is_all is False and sentence['status'] != 'approved':
                translation = ""

            entry = polib.POEntry(
                msgid=unicode(sentence['source_sentence'].strip()),
                msgstr=unicode(translation),
                tcomment=unicode(sentence['sentenceID'].strip()),
                occurrences=sentence['source_location']
                )
            po.append(entry)
    return getattr(po, '__unicode__')()

def generate_all_po_files(source_language, target_language, db, is_all):
    ''' goes through all of the files in the database for a pair of langauges and
    writes them all out to fresh po files. It then tars them up before returning
    the value of the tar
    :param string source_language: language to translate from
    :param string target_language: language to translate to
    :param database db: the instance of the database
    :param boolean is_all: whether or not you want all or just approved translations
    '''
    file_list = db['files'].find({'source_language': source_language,
                                  'target_language': target_language},
                                 {'_id': 1, 'file_path': 1})
    tar_string = cStringIO.StringIO()
    tar = tarfile.open(mode='w', fileobj=tar_string)
    for f in file_list:
        logger.debug("tarring " + f['file_path'])
        text = generate_fresh_po_text(f['file_path'], source_language, target_language, db, is_all)
        fake_file = cStringIO.StringIO(text)
        fake_tarinfo = tarfile.TarInfo(f['file_path']+'.po')
        fake_tarinfo.size = len(text)
        tar.addfile(fake_tarinfo, fake_file)
    tar.close()
    return tar_string.getvalue()
