#!/usr/bin/env python
"""Runs MongoDB jstests.

Usage:
        rst_tester <test.js>...
        
        Options:
                -h --help        Show this help text.
                
"""
import os
import subprocess
from subprocess import PIPE
import time
import unittest

from docopt import docopt


FNULL = open(os.devnull, 'w')
MONGOD_PORT = 20000


def test_factory():
    class MongoTestCase(unittest.TestCase):
        @classmethod
        def setUpClass(self):
            # TODO: Add small files flag
            # TODO: Add timeout and retry logic
            self.mongod = subprocess.Popen('mongod --port {}'.format(MONGOD_PORT), shell=True, stdout=FNULL)
            time.sleep(1)

        @classmethod
        def tearDownClass(self):
            self.mongod.kill()

    return MongoTestCase


def addTest(cls, js_test):
    def test(self):
        # return_code = subprocess.call("mongo {} --port {}".format(js_test, MONGOD_PORT), shell=True)  
        # TODO: Replace with check_call
        mongo = subprocess.Popen("mongo {} --port {}".format(js_test, MONGOD_PORT), shell=True, stdout=PIPE)
        stdout, _ = mongo.communicate()
        return_code = mongo.returncode
        success = 0

        # TODO nicer error message...
        self.assertEqual(return_code, success, "Test {} failed with output:\n{}".format(js_test, stdout))

    setattr(cls, js_test, test)


def main(tests):
    testSuite = unittest.TestSuite()

    t = test_factory()

    for test in tests:
        addTest(t, test)
        testSuite.addTest(t(test))

    unittest.TextTestRunner(verbosity=2).run(testSuite)


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['<test.js>'])
