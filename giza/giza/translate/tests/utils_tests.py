import unittest
import logging
import shutil
import os

from giza.translate.utils import flip_text_direction, merge_files, get_file_list

logger = logging.getLogger('giza.translate.corpora_tests')

class ListFilesTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(ListFilesTestCase, self).__init__(*args, **kwargs)

    def test_simple(self):
        self.assertEqual(get_file_list("test_files/test_dir", ['txt', 'yaml']), ['test_files/test_dir/f2.txt','test_files/test_dir/f1.txt','test_files/test_dir/f5.yaml','test_files/test_dir/d1/f4.txt'])

    def test_single(self):
        self.assertEqual(get_file_list("test_files/test_dir/f1.txt", ['txt']), ['test_files/test_dir/f1.txt'])

    def test_bad_file(self):
        with self.assertRaises(SystemExit):
            get_file_list("temp_files/mergdfadafadfaed.txt",['txt'])


class MergeTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(MergeTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        os.makedirs("temp_files")

    def tearDown(self):
        logger.info('tear down')
        shutil.rmtree("temp_files", ignore_errors=True)

    def test_simple(self):
        merge_files("test_files/merged.txt", ["test_files/f1", "test_files/f2", "test_files/f3"], ["+ ","- ", "~ "])
        with open("test_files/merged.txt") as f:
            self.assertEqual(f.read().strip(), "+ 1a\n- 2a\n~ 3a\n\n+ 1b\n- 2b\n~ 3b\n\n+ \n- 2c\n~ 3c\n\n+ 1c\n- 2d")

    def test_empty(self):
        merge_files("temp_files/merged.txt", ["test_files/empty.txt"], ["+ "])
        with open("temp_files/merged.txt") as f:
            self.assertEqual(f.read().strip(), "")

    def test_annotation_failure(self):
        with self.assertRaises(SystemExit):
            merge_files("temp_files/merged.txt", ["test_files/f1", "test_files/f2"], ["+ "])

    def test_bad_file(self):
        with self.assertRaises(SystemExit):
            merge_files("temp_files/merged.txt", ["test_files/fdafda1"], ["+ "])

class FlipTextTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(FlipTextTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        os.makedirs("temp_files")

    def tearDown(self):
        logger.info('tear down')
        shutil.rmtree("temp_files", ignore_errors=True)

    def test_simple(self):
        flip_text_direction("test_files/flip_text.txt", "temp_files/flipped.txt")
        with open("temp_files/flipped.txt") as f:
            self.assertEqual(f.read().strip(), "haduj ,olleh\nuoy era woh ,ih\n\na\ncb\ndoog")

    def test_empty(self):
        flip_text_direction("test_files/empty.txt", "temp_files/flipped.txt")
        with open("temp_files/flipped.txt") as f:
            self.assertEqual(f.read().strip(), "")

    def test_bad_file(self):
        with self.assertRaises(SystemExit):
            flip_text_direction("test_files/empdfadfadty.txt", "temp_files/flipped.txt")
