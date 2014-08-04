import unittest
import logging
import shutil
import os

import polib

from giza.serialization import ingest_yaml_doc
from giza.translate.translation import po_file_untranslated_to_text, extract_all_untranslated_po_entries, fill_po_file, write_po_files
from giza.translate.utils import get_file_list

logger = logging.getLogger('giza.translate.translation_tests')
TEST_PATH = os.path.abspath(os.path.join('..', os.path.dirname(__file__)))


class ExtractOnePoTestCase(unittest.TestCase):

    def setUp(self):
        os.makedirs(TEST_PATH+"/temp_files")

    def tearDown(self):
        logger.info('tear down')
        shutil.rmtree(TEST_PATH+"/temp_files", ignore_errors=True)

    def test_aggregation(self):
        with open(TEST_PATH+"/temp_files/source","w") as f:
            po_file_untranslated_to_text(f, TEST_PATH+"/test_files/docs/aggregation.po")
        with open(TEST_PATH+"/temp_files/source") as f:
            self.assertEqual(f.read().strip(), "Aggregation\nA high-level introduction to aggregation.\nIntroduces the use and operation of the data aggregation modalities available in MongoDB.")

    def test_admin(self):
        with open(TEST_PATH+"/temp_files/source","w") as f:
            po_file_untranslated_to_text(f, TEST_PATH+"/test_files/docs/administration.po")
        with open(TEST_PATH+"/temp_files/source") as f:
            self.assertEqual(f.read().strip(), "Administration")


class ExtractMultiplePoTestCase(unittest.TestCase):

    def setUp(self):
        os.makedirs(TEST_PATH+"/temp_files")

    def tearDown(self):
        logger.info('tear down')
        shutil.rmtree(TEST_PATH+"/temp_files", ignore_errors=True)

    def test_aggregation(self):
        po_file_list = get_file_list(TEST_PATH+"/test_files/docs",["po","pot"])
        extract_all_untranslated_po_entries(po_file_list,TEST_PATH+"/temp_files")
        with open(TEST_PATH+"/temp_files/source") as f:
            self.assertEqual(f.read().strip(), "Aggregation\nA high-level introduction to aggregation.\nIntroduces the use and operation of the data aggregation modalities available in MongoDB.\nAdministration")


class FillOnePoTestCase(unittest.TestCase):

    def setUp(self):
        os.makedirs(TEST_PATH+"/temp_files")
        shutil.copytree(TEST_PATH+"/test_files/docs", TEST_PATH+"/temp_files/docs")

    def tearDown(self):
        logger.info('tear down')
        shutil.rmtree(TEST_PATH+"/temp_files", ignore_errors=True)

    def test_administration(self):
        fill_po_file(TEST_PATH+"/temp_files/docs/administration.po","1", 0)
        f1 = polib.pofile(TEST_PATH+"/temp_files/docs/administration.po")
        f2 = polib.pofile(TEST_PATH+"/test_files/filled_docs/administration.po")
        for l1, l2 in zip(f1,f2):
            self.assertEqual(l1, l2)

    def test_aggregation(self):
        fill_po_file(TEST_PATH+"/temp_files/docs/aggregation.po","2\n3\n4", 1)
        f1 = polib.pofile(TEST_PATH+"/temp_files/docs/aggregation.po")
        f2 = polib.pofile(TEST_PATH+"/test_files/filled_docs/aggregation.po")
        for l1, l2 in zip(f1,f2):
            self.assertEqual(l1, l2)

class FillMultiplePoTestCase(unittest.TestCase):

    def setUp(self):
        os.makedirs(TEST_PATH+"/temp_files")
        shutil.copytree(TEST_PATH+"/test_files/docs", TEST_PATH+"/temp_files/docs")

    def tearDown(self):
        logger.info('tear down')
        shutil.rmtree(TEST_PATH+"/temp_files", ignore_errors=True)

    def test_files(self):
        po_file_list = get_file_list(TEST_PATH+"/temp_files/docs",["po","pot"])
        write_po_files(po_file_list,TEST_PATH+"/test_files/doc_filler.txt")
        f1 = polib.pofile(TEST_PATH+"/temp_files/docs/aggregation.po")
        f2 = polib.pofile(TEST_PATH+"/test_files/filled_docs/aggregation.po")
        for l1, l2 in zip(f1,f2):
            self.assertEqual(l1, l2)
        f1 = polib.pofile(TEST_PATH+"/temp_files/docs/administration.po")
        f2 = polib.pofile(TEST_PATH+"/test_files/filled_docs/administration.po")
        for l1, l2 in zip(f1,f2):
            self.assertEqual(l1, l2)
