import sys
import os.path
import models
import logging
import re

import polib
from pymongo import MongoClient

from giza.translate.utils import get_file_list

'''
This module takes the po files and writes the sentences
to mongodb. This is meant to be used after translate_po.py
The file should have each entry from the given username
translated and each other entry untranslated. For every group
of po files you input them with the appropriate username and status
'''

logger = logging.getLogger('verifier.app.po_to_mongo')

def write_po_file_to_mongo(po_fn, userID, status, source_language, target_language, po_root, db):
    '''write a po_file to mongodb
    :param string po_fn: the file name of the current pofile
    :param string userID: the ID of the user that translated the po file
    :param string status: the status of the translations
    :param string source_language: The source_language of the translations
    :param string target_language: The target_language of the translations
    :param string po_root: the root of the po_files
    :param database db: the database that you want to write to
    '''
    po = polib.pofile(po_fn)
    rel_fn = os.path.relpath(po_fn, po_root)
    rel_fn = os.path.splitext(rel_fn)[0]
    f = models.File({ u'file_path': rel_fn,
                      u'priority': 0,
                      u'source_language': source_language,
                      u'target_language': target_language }, curr_db=db)

    reg = re.compile('^:[a-zA-Z0-9]+:`(?!.*<.*>.*)[^`]*`$')
    for idx, entry in enumerate(po.translated_entries()):
        sentence_status = status
        match = re.match(reg, entry.msgstr.encode('utf-8'))
        if match is not None and match.group() == entry.msgstr.encode('utf-8'):
            sentence_status = "approved"

        t = models.Sentence({ u'source_language': source_language,
                              u'source_sentence': entry.msgid.encode('utf-8'),
                              u'sentenceID': entry.tcomment.encode('utf-8'),
                              u'sentence_num': idx,
                              u'fileID': f._id,
                              u'target_sentence': entry.msgstr.encode('utf-8'),
                              u'target_language': target_language,
                              u'userID': userID,
                              u'status': sentence_status,
                              u'update_number': 0 }, curr_db=db)
        t.save()
    f.get_num_sentences()

def put_po_files_in_mongo(path, username, status, source_language, target_language, db_host, db_port, db_name):
    '''go through directories and write the po file to mongo
    :param path: the path to the po_files
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
        write_po_file_to_mongo(fn, userID, status, source_language,
                    target_language, path, db)


def main():
    if len(sys.argv) < 8:
        print "Usage: python", ' '.join(sys.argv), "<path/to/*.po> <username> <status> <language> <host> <port> <dbname>"
        return
    put_po_files_in_mongo(sys.argv[1],sys.argv[2], sys.argv[3], u'en', sys.argv[4], sys.argv[5], int(sys.argv[6]), sys.argv[7])

if __name__ == "__main__":
    main()

