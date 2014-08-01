import unittest
import logging
import shutil
import os

from giza.serialization import ingest_yaml_doc
from giza.config.corpora import CorporaConfig
from giza.translate.corpora import create_hybrid_corpora, create_corpus_from_po, create_corpus_from_dictionary

logger = logging.getLogger('giza.translate.corpora_tests')

class DictToCorpusTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(DictToCorpusTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        os.makedirs("temp_files")

    def tearDown(self):
        logger.info('tear down')
        shutil.rmtree("temp_files", ignore_errors=True)

    def test_english(self):
        create_corpus_from_dictionary("test_files/dict.txt", "temp_files/source.txt", "temp_files/target.txt")
        with open("temp_files/source.txt") as f:
            self.assertEqual(f.read().strip(), "April\nApr\nAugust\nAug")

    def test_spanish(self):
        create_corpus_from_dictionary("test_files/dict.txt", "temp_files/source.txt", "temp_files/target.txt")
        with open("temp_files/target.txt") as f:
            self.assertEqual(f.read().strip(), "abril\nabril\nagosto\nagosto")

class PoToCorpusTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(PoToCorpusTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        os.makedirs("temp_files")

    def tearDown(self):
        logger.info('tear down')
        shutil.rmtree("temp_files", ignore_errors=True)

    def test_english(self):
        create_corpus_from_po("test_files/about.po", "temp_files/source.txt", "temp_files/target.txt")
        with open("temp_files/source.txt") as f:
            self.assertEqual(f.read().strip(), "About MongoDB Documentation\nLicense")

    def test_spanish(self):
        create_corpus_from_po("test_files/about.po", "temp_files/source.txt", "temp_files/target.txt")
        with open("temp_files/target.txt") as f:
            self.assertEqual(f.read().strip(), "Acerca de la documentacion de MongoDB\nLicencia")


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


class UnevenCorpusTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(UnevenCorpusTestCase, self).__init__(*args, **kwargs)
        self.conf_file = "configs_test/uneven_corpora.yaml"

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
            self.assertEqual(f.read().strip(), "e1-l\ne2-l\ne3-l\ne4-l\ne5-l\ne6-l\ne7-l\ne8-l\ne9-l\ne10-l\ne11-l\ne12-l\ne13-l\ne14-l\ne15-l\ne1-m\ne2-m\ne3-m\ne1-m\ne2-m\ne3-m\ne1-m\ne2-m\ne3-m\ne1-m\ne2-m\ne3-m\ne1-m\ne2-m\ne3-m")

    def test_spanish_train(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/train.en-es.es") as f:
            self.assertEqual(f.read().strip(), "s1-l\ns2-l\ns3-l\ns4-l\ns5-l\ns6-l\ns7-l\ns8-l\ns9-l\ns10-l\ns11-l\ns12-l\ns13-l\ns14-l\ns15-l\ns1-m\ns2-m\ns3-m\ns1-m\ns2-m\ns3-m\ns1-m\ns2-m\ns3-m\ns1-m\ns2-m\ns3-m\ns1-m\ns2-m\ns3-m")

    def test_english_tune(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/tune.en-es.en") as f:
            self.assertEqual(f.read().strip(), "e16-l\ne17-l\ne18-l\ne19-l\ne4-m\ne5-m\ne6-m\ne7-m\ne4-m\ne5-m")

    def test_spanish_tune(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/tune.en-es.es") as f:
            self.assertEqual(f.read().strip(), "s16-l\ns17-l\ns18-l\ns19-l\ns4-m\ns5-m\ns6-m\ns7-m\ns4-m\ns5-m")

    def test_english_test(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/test.en-es.en") as f:
            self.assertEqual(f.read().strip(), "e20-l\ne20-l\ne8-m\ne9-m\ne10-m")

    def test_spanish_test(self):
        create_hybrid_corpora(self.cconf)
        with open("temp_files/test.en-es.es") as f:
            self.assertEqual(f.read().strip(), "s20-l\ns20-l\ns8-m\ns9-m\ns10-m")


if __name__ == '__main__':
    unittest.main()
