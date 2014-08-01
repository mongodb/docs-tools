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
        self.conf_file = "test_configs/one_corpus.yaml"

    def setUp(self):
        if os.path.exists("temp_files") is False:
            os.makedirs("temp_files")
        self.cconf = ingest_yaml_doc(self.conf_file)
        self.cconf = CorporaConfig(self.cconf)

    def tearDown(self):
        logger.info('tear down')
        shutil.rmtree("temp_files", ignore_errors=True)

    def test_english_train(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/train.en-es.en") as f:
            self.assertEqual(f.read(), "hello")

    def test_spanish_train(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/train.en-es.es") as f:
            self.assertEqual(f.read(), "hola")

    def test_english_tune(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/tune.en-es.en") as f:
            self.assertEqual(f.read(), "")

    def test_spanish_tune(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/tune.en-es.en") as f:
            self.assertEqual(f.read(), "")

    def test_english_test(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/test.en-es.en") as f:
            self.assertEqual(f.read(), "")

    def test_spanish_test(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/test.en-es.en") as f:
            self.assertEqual(f.read(), "")

if __name__ == '__main__':
    unittest.main()
