import giza.configuration

from unittest import TestCase

class TestGiza(TestCase):
    @classmethod
    def setUp(self):
        self.conf = giza.configuration.Configuration()

        self.result = [ 1, 1, 2, 3, 5, 8 ]

    def test_baseline(self):
        self.conf.baseline = [ 1, 1, 2, 3, 5, 8 ]

        self.assertEqual(self.result, self.conf.baseline)

    def test_subdoc_type(self):
        self.conf.base = 1

        self.assertEqual(self.conf.base, 1)
