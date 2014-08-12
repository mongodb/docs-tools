import time
import atexit
import shutil
import tempfile
import unittest
import subprocess
import logging
import os
from random import randint

import pymongo

from pharaoh.utils import load_json
from pharaoh.app.models import Sentence, User, File

MONGODB_TEST_PORT = 31415
PATH_TO_MONGOD = '/home/wisdom/mongodb/2.6.0-rc0'
DBNAME = 'veritest'

logger = logging.getLogger('pharaoh.test_verifier')
TEST_PATH = os.path.abspath(os.path.join('..', os.path.dirname(__file__)))

class MongoTemporaryInstance(object):
    '''Singleton to manage a temporary MongoDB instance

    Use this for testing purpose only. The instance is automatically destroyed
    at the end of the program.
    Courtesy of: http://blogs.skicelab.com/maurizio/python-unit-testing-and-mongodb.html
    '''
    _instance = None

    @classmethod
    def get_instance(cls):
        '''This method gets an instance that's destroyed at the end of
        the program'''
        if cls._instance is None:
            cls._instance = cls()
            atexit.register(cls._instance.shutdown)
        return cls._instance

    def __init__(self):
        self._tmpdir = tempfile.mkdtemp()
        logger.info(self._tmpdir)
        self._process = subprocess.Popen('{0}/mongod --bind_ip localhost --port {1} --dbpath {2} --nojournal --nohttpinterface --noauth --smallfiles --syncdelay 0 --maxConns 10 --nssize 1'.format(PATH_TO_MONGOD, MONGODB_TEST_PORT, self._tmpdir), shell=True, executable='/bin/bash')
        #      wait for the instance to be ready
        #      Mongo is ready in a glance, we just wait to be able to open a
        #      Connection.

        for i in range(3):
            time.sleep(1)
            try:
                self._client = pymongo.MongoClient('localhost', MONGODB_TEST_PORT)
            except pymongo.errors.ConnectionFailure:
                continue
            else:
                break
        else:
            self.shutdown()
            assert False, 'Cannot connect to the mongodb test instance'

    @property
    def client(self):
        return self._client

    def shutdown(self):
        '''This method destroys the process and the instance'''
        if self._process:
            self._process.terminate()
            self._process.wait()
            self._process = None
            shutil.rmtree(self._tmpdir, ignore_errors=True)


class TestCase(unittest.TestCase):
    '''TestCase with an embedded MongoDB temporary instance.

    Each test runs on a temporary instance of MongoDB. Please note that
    these tests are not thread-safe and different processes should set a
    different value for the listening port of the MongoDB instance with the
    settings `MONGODB_TEST_PORT`.

    A test can access the connection using the attribute `conn`.

    '''
    db_init_files = [os.path.join(TEST_PATH, 'test_files', 'translations.json'),
                     os.path.join(TEST_PATH, 'test_files', 'users.json'),
                     os.path.join(TEST_PATH, 'test_files', 'files.json')]

    def __init__(self, *args, **kwargs):
        super(TestCase, self).__init__(*args, **kwargs)
        self.db_inst = MongoTemporaryInstance.get_instance()
        self.client = self.db_inst.client
        self.db = self.client[DBNAME]

    def sentence(self, id=None):
        '''This method wraps around the sentence creator to provide
        the correct db'''
        s = Sentence(oid=id, curr_db=self.db)
        return s

    def user(self, id=None):
        '''This method wraps around the user creator to provide
        the correct db'''
        u = User(oid=id, curr_db=self.db)
        return u

    def file(self, id=None):
        '''This method wraps around the file creator to provide
        the correct db'''
        f = File(oid=id, curr_db=self.db)
        return f

    def jumble_data(self):
        '''This method does random updates to the data'''
        for i in range(randint(0, 5)):
            try:
                s = self.sentence(id='s{0}'.format(randint(1, 3)))
                u = self.user(id='u{0}'.format(randint(1, 3)))
                s.edit(u, "foo{0}".format(i))
            except Exception:
                continue

        for i in range(randint(0, 3)):
            try:
                s = self.sentence(id='s{0}'.format(randint(1, 3)))
                u = self.user(id='u{0}'.format(randint(1, 3)))
                s.approve(u)
            except Exception:
                continue


    def setUp(self):
        '''This method sets up the test by deleting all of the databases
        and reloading them'''
        super(TestCase, self).setUp()

        for db_name in self.client.database_names():
            self.client.drop_database(db_name)

        for f in self.db_init_files:
            load_json(f, self.db)

    def test_setup(self):
        '''This test tests that the database sets up properly'''
        pass

    def test_edit(self):
        '''This test tests a simple edit works as it should'''
        s = self.sentence(id=u's1')
        s_old = self.sentence(id=u's1')
        judah = self.user(id=u'u2')
        s.edit(judah, u'foo bar')
        s = self.sentence(id=u's1')
        judah = self.user(id=u'u2')
        self.assertEquals(s.update_number, s_old.update_number+1)
        self.assertEquals(s.target_sentence, u'foo bar')
        self.assertEquals(s.status, u'reviewed')

        self.assertEquals(judah.num_reviewed, 1)

    def test_approve(self):
        '''This method tests that the approve command works properly'''
        s = self.sentence(id=u's1')
        s_old = self.sentence(id=u's1')
        judah = self.user(id=u'u2')
        judah_old = self.user(id=u'u2')
        moses_old = self.user(id=u'u1')
        s.approve(judah)
        s = self.sentence(id=u's1')
        judah = self.user(id=u'u2')
        moses = self.user(id=u'u1')
        self.assertEquals(s.update_number, s_old.update_number+1)
        self.assertTrue(u'u2' in s.approvers)

        self.assertEquals(judah.num_user_approved, judah_old.num_user_approved + 1)
        self.assertEquals(moses.num_got_approved, moses_old.num_got_approved + 1)

    def test_unapprove(self):
        '''This method tests that the approve command works properly'''
        s_pre = self.sentence(id=u's1')
        judah_pre = self.user(id=u'u2')
        s_pre.approve(judah_pre)

        s = self.sentence(id=u's1')
        s_old = self.sentence(id=u's1')
        judah = self.user(id=u'u2')
        judah_old = self.user(id=u'u2')
        moses_old = self.user(id=u'u1')
        s.unapprove(judah)
        s = self.sentence(id=u's1')
        judah = self.user(id=u'u2')
        moses = self.user(id=u'u1')
        self.assertEquals(s.update_number, s_old.update_number+1)
        self.assertFalse(u'u2' in s.approvers)

        self.assertEquals(judah.num_user_approved, judah_old.num_user_approved - 1)
        self.assertEquals(moses.num_got_approved, moses_old.num_got_approved - 1)

    def test_sentence_approved(self):
        '''This method tests that if a sentence is approved twice
        it gets approved'''
        s = self.sentence(id=u's3')
        judah = self.user(id=u'u2')
        s.approve(judah)
        s = self.sentence(id=u's3')
        self.assertEquals(s.status, 'approved')

    def test_approve_twice(self):
        '''This method tests that you can't approve a sentence twice'''
        s_pre = self.sentence(id=u's1')
        judah_pre = self.user(id=u'u2')
        s_pre.approve(judah_pre)

        s = self.sentence(id=u's1')
        judah = self.user(id=u'u2')
        with self.assertRaises(Exception):
            s.approve(judah)

    def test_approve_own_edit(self):
        '''This method tests that you can't approve a setence
        you edited last'''
        s_pre = self.sentence(id=u's1')
        judah_pre = self.user(id=u'u2')
        s_pre.edit(judah_pre, "edited")

        s = self.sentence(id=u's1')
        judah = self.user(id=u'u2')
        with self.assertRaises(Exception):
            s.approve(judah)

    def test_unapprove_no_approve(self):
        '''This method tests that you can't unapprove a
        sentence you haven't approved'''
        s = self.sentence(id=u's1')
        judah = self.user(id=u'u2')
        with self.assertRaises(Exception):
            s.unapprove(judah)

    def test_edit_own_approve(self):
        '''This method tests that you can't edit something you've approved'''
        s_pre = self.sentence(id=u's1')
        judah_pre = self.user(id=u'u2')
        s_pre.approve(judah_pre)

        s = self.sentence(id=u's1')
        judah = self.user(id=u'u2')
        with self.assertRaises(Exception):
            s.edit(judah, "edited")

    def test_edit_no_change(self):
        '''This method tests that you can't make an edit with no change'''
        s = self.sentence(id=u's1')
        judah = self.user(id=u'u2')
        with self.assertRaises(Exception):
            s.edit(judah, s.target_sentence)

    def test_edit_lock(self):
        '''This method tests that you can't make an edit with a lock'''
        s = self.sentence(id=u's1')
        judah = self.user(id=u'u2')
        s.edit(judah, "foo bar")
        wisdom = self.user(id=u'u3')
        with self.assertRaises(Exception):
            s.edit(wisdom, s.target_sentence)

if __name__ == '__main__':
    unittest.main()