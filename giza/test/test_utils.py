import unittest
import logging
import shutil
import os

from giza.translate.utils import flip_text_direction, merge_files, get_file_list

logger = logging.getLogger('test.test_utils')
TEST_PATH = os.path.abspath(os.path.join('..', os.path.dirname(__file__)))


class ListFilesTestCase(unittest.TestCase):

    def test_simple(self):
        file_list = get_file_list(os.path.join(TEST_PATH, "test_files", "test_dir"), ['txt', 'yaml'])
        file_list.sort()
        self.assertEqual(file_list, [os.path.join(TEST_PATH, "test_files", "test_dir", "d1", "f4.txt"),
                                     os.path.join(TEST_PATH, "test_files", "test_dir", "f1.txt"),
                                     os.path.join(TEST_PATH, "test_files", "test_dir", "f2.txt"),
                                     os.path.join(TEST_PATH, "test_files", "test_dir", "f5.yaml")])

    def test_single(self):
        self.assertEqual(get_file_list(os.path.join(TEST_PATH, "test_files", "test_dir", "f1.txt"), ['txt']),
                         [os.path.join(TEST_PATH, "test_files", "test_dir", "f1.txt")])

    def test_bad_file(self):
        self.assertEqual(get_file_list(os.path.join(TEST_PATH, "temp_files", "mergdfadafadfaed.txt"),['txt']),[])


class MergeTestCase(unittest.TestCase):

    def setUp(self):
        os.makedirs(os.path.join(TEST_PATH, "temp_files"))

    def tearDown(self):
        logger.info('tear down')
        shutil.rmtree(os.path.join(TEST_PATH, "temp_files"), ignore_errors=True)

    def test_simple(self):
        merge_files(os.path.join(TEST_PATH, "test_files", "merged.txt"),
                   [os.path.join(TEST_PATH, "test_files", "f1"),
                    os.path.join(TEST_PATH, "test_files", "f2"),
                    os.path.join(TEST_PATH, "test_files", "f3")], ["+ ","- ", "~ "])
        with open(os.path.join(TEST_PATH, "test_files", "merged.txt")) as f:
            self.assertEqual(f.read().strip(), "+ 1a\n- 2a\n~ 3a\n\n+ 1b\n- 2b\n~ 3b\n\n+ \n- 2c\n~ 3c\n\n+ 1c\n- 2d")

    def test_empty(self):
        merge_files(os.path.join(TEST_PATH, "temp_files", "merged.txt"),
                   [os.path.join(TEST_PATH, "test_files", "empty.txt")], ["+ "])
        with open(os.path.join(TEST_PATH, "temp_files", "merged.txt")) as f:
            self.assertEqual(f.read().strip(), "")

    def test_annotation_failure(self):
        with self.assertRaises(Exception):
            merge_files(os.path.join(TEST_PATH, "temp_files", "merged.txt"),
                       [os.path.join(TEST_PATH, "test_files", "f1"),
                        os.path.join(TEST_PATH, "test_files", "f2")], ["+ "])

    def test_bad_file(self):
        with self.assertRaises(Exception):
            merge_files(os.path.join(TEST_PATH, "temp_files", "merged.txt"),
                       [os.path.join(TEST_PATH, "test_files", "fdafda1")], ["+ "])

class FlipTextTestCase(unittest.TestCase):

    def setUp(self):
        os.makedirs(os.path.join(TEST_PATH, "temp_files"))

    def tearDown(self):
        logger.info('tear down')
        shutil.rmtree(os.path.join(TEST_PATH, "temp_files"), ignore_errors=True)

    def test_simple(self):
        flip_text_direction(os.path.join(TEST_PATH, "test_files", "flip_text.txt"),
                            os.path.join(TEST_PATH, "temp_files", "flipped.txt"))
        with open(os.path.join(TEST_PATH, "temp_files", "flipped.txt")) as f:
            self.assertEqual(f.read().strip(), "haduj ,olleh\nuoy era woh ,ih\n\na\ncb\ndoog")

    def test_empty(self):
        flip_text_direction(os.path.join(TEST_PATH, "test_files", "empty.txt"),
                            os.path.join(TEST_PATH, "temp_files", "flipped.txt"))
        with open(os.path.join(TEST_PATH, "temp_files", "flipped.txt")) as f:
            self.assertEqual(f.read().strip(), "")

    def test_bad_file(self):
        with self.assertRaises(Exception):
            flip_text_direction(os.path.join(TEST_PATH, "test_files", "empdfadfadty.txt"),
                                os.path.join(TEST_PATH, "temp_files", "flipped.txt"))

