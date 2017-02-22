import unittest
import tempfile

import giza.libgiza.config


class TestConfigurationObjectPersistance(unittest.TestCase):
    def setUp(self):
        self.conf = giza.libgiza.config.ConfigurationBase

    def test_create_empty_file(self):
        with tempfile.NamedTemporaryFile(suffix=".yaml") as f:
            with self.conf.persisting(f.name) as data:
                data.state["_test_data"] = "42"

            d = self.conf(f.name)

            self.assertEquals(d._test_data, "42")

    def test_operations_with_existing_data(self):
        with tempfile.NamedTemporaryFile(suffix=".yaml") as f:
            with self.conf.persisting(f.name) as data:
                data.state["_test_data"] = 42

            with self.conf.persisting(f.name) as data:
                self.assertEquals(data._test_data, 42)

                data._test_data += 1
                self.assertEquals(data._test_data, 43)

                data.state["_test_data"] = data._test_data

            d = self.conf(f.name)
            self.assertEquals(d._test_data, 43)


class TestConfigurationObjectMembership(unittest.TestCase):
    def setUp(self):
        self.conf = giza.libgiza.config.ConfigurationBase()

    def test_internal_values(self):
        self.assertNotIn("_foo", self.conf)
        self.assertNotIn("_foo", self.conf.state)

        self.conf._foo = 42

        self.assertIn("_foo", self.conf)
        self.assertNotIn("_foo", self.conf.state)
