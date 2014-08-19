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

import datetime

from flask_app import app, db

def get_sentences_in_file(fp, source_language, target_language, curr_db=db):
    '''This function  gets all of the sentences in the given file
    :param dataabase db: database
    :param string fp: path to the file
    :param string source_language: source language
    :param string target_language: target language
    :returns: cursor of sentences
    '''
    app.logger.debug(fp)
    f = curr_db['files'].find_one({'source_language': source_language,
                                   'target_language': target_language,
                                   'file_path': fp},
                                   {'_id': 1, 'edition':1})
    sentences = curr_db['translations'].find({'fileID': f[u'_id'],
                                              'file_edition': f[u'edition']},
                                             {'_id': 1,
                                              'source_sentence': 1,
                                              'target_sentence': 1,
                                              'approvers': 1,
                                              'status': 1,
                                              'userID': 1} ).sort('sentence_num', 1)
    return sentences

def get_languages(curr_db=db):
    '''This function gets all of the unique target languages
    :param database db: database
    :returns: cursor of languages
    '''
    languages = curr_db['translations'].find().distinct('target_language')
    return languages

def get_fileIDs(source_language, target_language, curr_db=db):
    '''This function  gets all of the file ids for a given pair of languages
    :param string db: database
    :param string source_language: source language
    :param string target_language: target language
    :returns: cursor of fileids
    '''
    return curr_db['files'].find({'source_language': source_language,
                                  'target_language': target_language},
                                 {'_id': 1}).sort('priority', 1)

def get_file_paths(curr_db=db):
    '''This function  gets all of the file ids for a given pair of languages
    :param string db: database
    :param string source_language: source language
    :param string target_language: target language
    :returns: cursor of fileids
    '''
    return curr_db['files'].distinct('file_path')


def get_files_for_page(page_number, num_files_per_page, fileIDs, curr_db=db):
    '''This function gets all of the stats for a list of files
    :param int page_number: current page number
    :param int num_files_per_page: number of files per page
    :param list fileIDS: list of file ids
    :param database db: database
    :returns: cursor of file names
    '''
    page_fileIDs = fileIDs.skip(((page_number-1)*num_files_per_page) if page_number > 0 else 0).limit(num_files_per_page)
    l = []
    for f in page_fileIDs:
        f = File(oid=f[u'_id'])
        if f.num_sentences == 0:
            continue
        data = {'file_path': f.file_path,
                'num_sentences': f.num_sentences,
                'num_reviewed': f.num_reviewed(),
                'num_approved': f.num_approved()}
        if data['num_sentences'] != data['num_approved']:
            l.append(data)

    return l


def audit(action, last_editor, current_user, doc, new_target_sentence=None, curr_db=db):
    ''' This function saves an audit of the event that occurred
    :param database db': database
    :param string action': edit, approve, or unapprove
    :param string last editor': id of the last person to edit the sentence before this action occurred
    :param string current user': id of the user who did the action
    :param string doc': original python dictionary of old data
    :param string new_target_sentence': new translation of the sentence, might be none if action is approved
    '''
    if action is 'edit':
        curr_db['audits'].insert({'action': action,
                                  'last_editor': last_editor,
                                  'current_user': current_user,
                                  'original_document': doc,
                                  'new_target_sentence': new_target_sentence,
                                  'timestamp': datetime.datetime.utcnow() })
    else:
        curr_db['audits'].insert({'action': action,
                                  'last_editor': last_editor,
                                  'current_user': current_user,
                                  'original_document': doc,
                                  'timestamp': datetime.datetime.utcnow() })

def find_file(source_language, target_language, file_path, curr_db=db):
    '''This function finds the record of a file by it's languages and file_path,
    which should ideally be unique. If these aren't unique this could create
    issues, but if they're not unique then you probably already have a problem.
    :param string source_language'
    :param string target_language'
    :param string file_path' path to the file you're trying to find
    :returns: File's record
    '''
    record = curr_db['files'].find_one({'source_language': source_language,
                                        'target_language': target_language,
                                        'file_path': file_path})
    return record

def find_sentence(source_language, target_language, sentenceID, curr_db=db):
    '''This function finds the record of a file by it's languages and id,
    which should ideally be unique. If these aren't unique this could create
    issues, but if they're not unique then you probably already have a problem.
    :param string source_language'
    :param string target_language'
    :param string sentenceID' the ID of the sentence
    :returns: sentence's record
    '''
    record = curr_db['translations'].find_one({'source_language': source_language,
                                               'target_language': target_language,
                                               'sentenceID': sentenceID}, sort=[('file_edition',-1)])
    return record


class File(object):
    '''This class models a file.
    It has a lock on it so no two people can edit the file at the same time. It has a priority to say how important translation it is
    It also has a set of languages
    '''
    def __init__(self, source=None, oid=None, curr_db=db):
        self.db = curr_db
        self.state = {u'file_path': None,
                      u'lock_exp': datetime.datetime.utcnow(),
                      u'lock_id': None,
                      u'priority': 0,
                      u'source_language': None,
                      u'target_language': None,
                      u'edition': 0,
                      u'num_sentences': -1}

        if source is not None:
            for k, v in source.items():
                if k not in self.state:
                    app.logger.error(k)
                    raise KeyError

            if ('source_language' in source) and ('target_language' in source) and ('file_path' in source):
                s = find_file(source['source_language'],
                              source['target_language'],
                              source['file_path'],
                              curr_db=self.db)
                if s is not None:
                    source = s
                    source['edition'] += 1
            for k, v in source.items():
                self.state[k] = v
            self.save()

        elif oid is not None:
            record = self.db['files'].find_one({'_id': oid})
            for k, v in record.items():
                self.state[k] = v

    def save(self):
        self.state[u'_id'] = self.db['files'].save(self.state)

    @property
    def file_path(self):
        return self.state[u'file_path']

    @property
    def edition(self):
        return self.state[u'edition']

    @property
    def priority(self):
        return self.state[u'priority']

    @property
    def target_language(self):
        return self.state[u'target_language']

    @property
    def source_language(self):
        return self.state[u'source_language']

    @property
    def _id(self):
        return self.state[u'_id']

    def grab_lock(self, userID):
        '''This method tries to grab the lock on the file. If it succeeds
        then it pushes the lock back and returns true, if it fails then it
        returns false
        :param string userID: _id of the user who is trying to grab the lock
        :returns: True or False if you grabbed the lock or not
        '''
        now = datetime.datetime.utcnow()
        time_diff =datetime.timedelta(minutes=app.config['SESSION_LENGTH'])
        if self.state[u'lock_exp'] < now:
            self.state[u'lock_exp'] = now + time_diff
            self.state[u'lock_id'] = userID
            self.save()
            return True
        elif self.state[u'lock_id'] == userID:
            self.state[u'lock_exp'] = now + time_diff
            self.save()
            return True
        else:
            return False

    def num_approved(self):
            return self.db['translations'].find({'fileID': self._id, 'file_edition': self.edition, 'status': 'approved'}).count()

    def num_reviewed(self):
            return self.db['translations'].find({'fileID': self._id, 'file_edition': self.edition, 'status': { '$in': ['reviewed', 'approved']}}).count()

    def get_num_sentences(self):
        self.state[u'num_sentences'] = self.db['translations'].find({'fileID': self._id, 'file_edition': self.edition}).count()
        self.save()
        return self.num_sentences

    @property
    def num_sentences(self):
        return self.state[u'num_sentences']

class Sentence(object):
    ''' This class models a sentence. A sentence has a user who last edited it,
    a pair of languages and sentences in those languages, a file and a sentence
    number in that file. It also has a status, and update number, and approvers.
    '''
    def __init__(self, source=None, oid=None, curr_db=db):
        self.db = curr_db
        self.state = {u'created_at': datetime.datetime.utcnow(),
                      u'userID': None,
                      u'source_language': None,
                      u'source_sentence': None,
                      u'sentence_num': -1,
                      u'fileID': None,
                      u'file_edition': 0,
                      u'sentenceID': None,
                      u'source_location': None,
                      u'target_sentence': None,
                      u'status': u'init',
                      u'update_number': 0,
                      u'target_language': None,
                      u'approvers': [] }

        if source is not None:
            for k, v in source.items():
                if k not in self.state:
                    app.logger.error(k)
                    raise KeyError
            if ('source_language' in source) and ('target_language' in source) and ('sentenceID' in source) and ('sentence_num' in source) and ('status' in source):
                # Checks if the sentence is already there
                s = find_sentence(source[u'source_language'],
                                  source[u'target_language'],
                                  source[u'sentenceID'],
                                  curr_db=self.db)
                if s is not None:
                    s[u'sentence_num'] = source['sentence_num']
                    s[u'file_edition'] = source['file_edition']
                    del s['_id']
                    # If it's there and not approved, use the old version; if the new one is approved use the new one
                    if not(source[u'status'] == 'approved' or (s[u'status'] == 'untranslated' and source[u'status'] != 'untranslated')):
                        source = s

            for k, v in source.items():
                self.state[k] = v
            self.save()
        elif oid is not None:
            record = self.db['translations'].find_one({'_id': oid})
            for k, v in record.items():
                self.state[k] = v

    def check_lock(self, userID):
        f = File(oid=self.fileID, curr_db=self.db)
        return f.grab_lock(userID)

    def edit(self, new_editor, new_target_sentence):
        '''This function edits the current sentence.
        :param string new_editor': The userID of the person who just edited it
        :param string new_target_sentence': new translation of the sentence
        '''
        if self.check_approver(new_editor._id):
            err = "Already approved sentence"
            app.logger.error(err)
            raise MyError(err, 403)
        if new_target_sentence == self.target_sentence:
            err = "No change made"
            app.logger.error(err)
            raise MyError(err, 403)
        if self.status is 'approved':
            err = "Can't edit approved sentence"
            app.logger.error(err)
            raise MyError(err, 403)

        f = File(oid=self.fileID, curr_db=self.db)
        if f.grab_lock(new_editor._id) is False:
            app.logger.error("can't edit without lock")
            raise LockError("Someone else is already editing this file", f.file_path, new_editor.username, self.target_language)

        audit("edit", self.userID, new_editor._id, self.state, new_target_sentence)
        self.increment_update_number()
        self.userID = new_editor._id
        self.target_sentence = new_target_sentence
        self.status = 'reviewed'
        self.state['approvers'] = []

        new_editor.increment_num_reviewed()
        self.save()
        new_editor.save()


    def approve(self, approver):
        '''This function approves the current sentence.
        :param string prev_editor: The userID of the person who last edited it
        :param string approver: The userID of the person who just approved it
        '''
        if approver._id == self.userID:
            err = "Can't approve own edit"
            app.logger.error(err)
            raise MyError(err, 403)
        if approver._id in self.approvers:
            err = "Can't approve sentence twice"
            app.logger.error(err)
            raise MyError(err, 403)
        if self.target_sentence == "" and self.source_sentence != "":
            err = "Can't approve empty sentence"
            app.logger.error(err)
            raise MyError(err, 403)

        f = File(oid=self.fileID, curr_db=self.db)
        if f.grab_lock(approver._id) is False:
            app.logger.error("can't approve without lock")
            raise LockError("Someone else is already editing this file", f.file_path, approver.username, self.target_language)

        prev_editor = User(oid=self.userID, curr_db=self.db)
        audit("approve", prev_editor._id, approver._id, self.state)
        self.increment_update_number()
        self.status = 'reviewed'
        approver.increment_user_approved()
        self.add_approver(approver._id)
        prev_editor.increment_got_approved()
        if approver.trust_level is 'full':
            self.status = 'approved'
        prev_editor.save()
        approver.save()
        self.save()

    def unapprove(self, unapprover):
        '''This function unapproves the current sentence.
        :param string prev_editor': The userID of the person who last edited it
        :param string unapprover': The userID of the person who just unapproved it
        '''
        if self.check_approver(unapprover._id) is False:
            err = "Never approved sentence"
            app.logger.error(err)
            raise MyError(err, 403)

        f = File(oid=self.fileID, curr_db=self.db)
        if f.grab_lock(unapprover._id) is False:
            app.logger.error("can't unapprove without lock")
            raise LockError("Someone else is already editing this file", f.file_path, unapprover.username, self.target_language)

        prev_editor = User(oid=self.userID, curr_db=self.db)
        audit("unapprove", prev_editor._id, unapprover._id, self.state)
        self.increment_update_number()
        self.remove_approver(unapprover._id)
        unapprover.decrement_user_approved()
        prev_editor.decrement_got_approved()
        prev_editor.save()
        unapprover.save()
        self.save()

    def save(self):
        self.state[u'_id'] = self.db['translations'].save(self.state)

    @property
    def target_language(self):
        return self.state[u'target_language']

    @target_language.setter
    def target_language(self, value):
        if value in (u'es', u'jp', u'cz'):
            self.state[u'target_language'] = value
        else:
            raise TypeError

    @property
    def source_language(self):
        return self.state[u'source_language']

    @source_language.setter
    def source_language(self, value):
        if value in (u'en'):
            self.state[u'source_language'] = value
        else:
            raise TypeError

    @property
    def userID(self):
        return self.state[u'userID']

    @userID.setter
    def userID(self, value):
        self.state[u'userID'] = value

    @property
    def status(self):
        return self.state[u'status']

    @status.setter
    def status(self, value):
        if value in (u'smt', u'reviewed', u'approved'):
            self.state[u'status'] = value
        else:
            raise TypeError

    @property
    def fileID(self):
        return self.state[u'fileID']

    @property
    def sentenceID(self):
        return self.state[u'sentenceID']

    @property
    def source_location(self):
        return self.state[u'source_location']

    @property
    def sentence_num(self):
        return self.state[u'sentence_num']

    @property
    def update_number(self):
        return self.state[u'update_number']

    @property
    def create_at(self):
        return self.state[u'created_at']

    @property
    def source_sentence(self):
        return self.state[u'source_sentence']

    @property
    def target_sentence(self):
        return self.state[u'target_sentence']

    @target_sentence.setter
    def target_sentence(self, value):
        self.state[u'target_sentence'] = value

    def increment_update_number(self):
        self.state[u'update_number'] += 1

    @property
    def approvers(self):
        return self.state[u'approvers']

    def num_approves(self):
        return len(self.state[u'approvers'])

    def add_approver(self, userID):
        if userID in self.state[u'approvers']:
            raise MyError("Can't approve sentence twice", 403)
        self.state[u'approvers'].append(userID)
        if self.num_approves() >= app.config['APPROVAL_THRESHOLD']:
            self.status = "approved"

    def remove_approver(self, userID):
        if userID not in self.state[u'approvers']:
            raise MyError("Never approved sentence", 403)

        self.state[u'approvers'].remove(userID)
        if self.num_approves() < app.config['APPROVAL_THRESHOLD']:
            self.status = "reviewed"

    def check_approver(self, userID):
        return userID in self.state[u'approvers']


class User(object):
    ''' This class models a user. A user has a username, a number of reviews,
    and number of sentences that the user approved and anumber of sentences
    that the user edited that were approved. A user also has a trust level
    specifying how much trust we put in them for their translations and approvals
    '''
    def __init__(self, source=None, oid=None, username=None, curr_db=db):
        self.db = curr_db
        self.state = {u'username': username,
                      u'num_reviewed': 0,
                      u'num_user_approved': 0,
                      u'num_got_approved': 0,
                      u'trust_level': 'basic'}

        if source is not None:
            for k, v in source.items():
                if k not in self.state:
                    app.logger.error(k)
                    raise KeyError

            for k, v in source.items():
                self.state[k] = v
            self.save()
        elif oid is not None:
            record = self.db['users'].find_one({'_id': oid})
            for k, v in record.items():
                self.state[k] = v
        elif username is not None:
            record = self.db['users'].find_one({'username': username})
            if record is None:
                db['users'].insert({"username": username, "num_reviewed": 0, "num_user_approved": 0, "num_got_approved":0, "trust_level": "basic"})
                record = self.db['users'].find_one({'username': username})
            for k, v in record.items():
                self.state[k] = v

    def save(self):
        app.logger.info(self.state)
        self.state[u'_id'] = self.db['users'].save(self.state)

    @property
    def _id(self):
        return self.state[u'_id']

    @property
    def username(self):
        return self.state[u'username']

    @property
    def num_translated(self):
        return self.state[u'num_reviewed']

    @property
    def num_reviewed(self):
        return self.state[u'num_reviewed']

    def increment_num_reviewed(self):
        self.state[u'num_reviewed'] += 1

    def decrement_num_reviewed(self):
        self.state[u'num_reviewed'] -= 1

    @property
    def num_user_approved(self):
        return self.state[u'num_user_approved']

    def increment_user_approved(self):
        self.state[u'num_user_approved'] += 1

    def decrement_user_approved(self):
        self.state[u'num_user_approved'] -= 1

    @property
    def num_got_approved(self):
        return self.state[u'num_got_approved']

    def increment_got_approved(self):
        self.state[u'num_got_approved'] += 1

    def decrement_got_approved(self):
        self.state[u'num_got_approved'] -= 1

    @property
    def trust_level(self):
        return self.state[u'trust_level']

    @trust_level.setter
    def trust_level(self, value):
        if value in (u'basic', u'partial', u'full'):
            self.state[u'trust_level'] = value
        else:
            raise TypeError

class MyError(Exception):
    def __init__(self, msg, code):
        self.msg = msg
        self.code = code

    def __str__(self):
        return self.msg

class LockError(Exception):
    def __init__(self, msg, file_path, username, target_language):
        self.msg = msg
        self.file_path = file_path
        self.username = username
        self.target_language = target_language
        self.code = 423

    def __str__(self):
        return self.msg
