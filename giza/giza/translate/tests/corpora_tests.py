import unittest
import logging
import shutil
import os

from giza.serialization import ingest_yaml_doc
from giza.config.corpora import CorporaConfig
from giza.translate.corpora import create_hybrid_corpora, create_corpus_from_po, create_corpus_from_dictionary

logger = logging.getLogger('giza.translate.tests')


class OneCorpusTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(OneCorpusTestCase, self).__init__(*args, **kwargs)
        self.conf_file = "configs_test/one_corpus.yaml"

    def setUp(self):
        self.cconf = ingest_yaml_doc(self.conf_file)
        self.cconf = CorporaConfig(self.cconf)

    def tearDown(self):
        logger.info('tear down')
        shutil.rmtree("temp_files", ignore_errors=True)

    def test_english_train(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/train.en-es.en") as f:
            self.assertEqual(f.read().strip(), "hello")

    def test_spanish_train(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/train.en-es.es") as f:
            self.assertEqual(f.read().strip(), "hola")

    def test_english_tune(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/tune.en-es.en") as f:
            self.assertEqual(f.read().strip(), "")

    def test_spanish_tune(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/tune.en-es.es") as f:
            self.assertEqual(f.read().strip(), "")

    def test_english_test(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/test.en-es.en") as f:
            self.assertEqual(f.read().strip(), "")

    def test_spanish_test(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/test.en-es.es") as f:
            self.assertEqual(f.read().strip(), "")

class EvenCorpusTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(EvenCorpusTestCase, self).__init__(*args, **kwargs)
        self.conf_file = "configs_test/even_corpora.yaml"

    def setUp(self):
        self.cconf = ingest_yaml_doc(self.conf_file)
        self.cconf = CorporaConfig(self.cconf)

    def tearDown(self):
        logger.info('tear down')
        shutil.rmtree("temp_files", ignore_errors=True)

    def test_english_train(self):
        print self.cconf
        create_hybrid_corpora(self.cconf)
        with open("temp_files/train.en-es.en") as f:
            self.assertEqual(f.read().strip(), "hello\ne1-m\ne2-m\ne3-m")

    def test_spanish_train(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/train.en-es.es") as f:
            self.assertEqual(f.read().strip(), "hola\ns1-m\ns2-m\ns3-m")

    def test_english_tune(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/tune.en-es.en") as f:
            self.assertEqual(f.read().strip(), "e4-m\ne5-m\ne6-m")

    def test_spanish_tune(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/tune.en-es.es") as f:
            self.assertEqual(f.read().strip(), "s4-m\ns5-m\ns6-m")

    def test_english_test(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/test.en-es.en") as f:
            self.assertEqual(f.read().strip(), "e7-m\ne8-m\ne9-m\ne10-m")

    def test_spanish_test(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/test.en-es.es") as f:
            self.assertEqual(f.read().strip(), "s7-m\ns8-m\ns9-m\ns10-m")

class HiddenCorpusTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(HiddenCorpusTestCase, self).__init__(*args, **kwargs)
        self.conf_file = "configs_test/hidden_corpora.yaml"

    def setUp(self):
        self.cconf = ingest_yaml_doc(self.conf_file)
        self.cconf = CorporaConfig(self.cconf)

    def tearDown(self):
        logger.info('tear down')
        shutil.rmtree("temp_files", ignore_errors=True)

    def test_english_train(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/train.en-es.en") as f:
            self.assertEqual(f.read().strip(), "hello\ne1-m\ne2-m\ne3-m")

    def test_spanish_train(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/train.en-es.es") as f:
            self.assertEqual(f.read().strip(), "hola\ns1-m\ns2-m\ns3-m")

    def test_english_tune(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/tune.en-es.en") as f:
            self.assertEqual(f.read().strip(), "")

    def test_spanish_tune(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/tune.en-es.es") as f:
            self.assertEqual(f.read().strip(), "")

    def test_english_test(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/test.en-es.en") as f:
            self.assertEqual(f.read().strip(), "")

    def test_spanish_test(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/test.en-es.es") as f:
            self.assertEqual(f.read().strip(), "")
if __name__ == '__main__':
    unittest.main()
