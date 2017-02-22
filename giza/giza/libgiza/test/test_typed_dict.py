"""
A collection of tests of the TypedDict specialized dictionary type which allows
us to specify types for of the the keys and values of a dictionary along with
validation methods to validate input on creation.

These tests ensure that TypedDicts behave as expected, which is to say, like
"vanilla" dicts, but that they also enforce their validation requirements (when
implemented.) and type checking (always.)
"""
import datetime
import sys
import unittest

import giza.libgiza.typed_dict
import giza.libgiza.error

if sys.version_info >= (3, 0):
    basestring = str


class TestTypedDictionaryObjectCreation(unittest.TestCase):
    def test_object_creation_returns_correctly_typed_values(self):
        d = giza.libgiza.typed_dict.TypedDict(key_type=basestring,
                                              value_type=bool)

        self.assertIsInstance(d, giza.libgiza.typed_dict.TypedDict)

        d = giza.libgiza.typed_dict.TypedDict(key_type=basestring,
                                              value_type=bool)

        self.assertIsInstance(d, giza.libgiza.typed_dict.TypedDict)

    def test_object_initialization_with_invalid_inputs(self):
        with self.assertRaises(TypeError):
            giza.libgiza.typed_dict.TypedDict()

        with self.assertRaises(TypeError):
            giza.libgiza.typed_dict.TypedDict("1", 2)

        with self.assertRaises(TypeError):
            giza.libgiza.typed_dict.TypedDict(bool, 2)

        with self.assertRaises(TypeError):
            giza.libgiza.typed_dict.TypedDict(2, bool)

        with self.assertRaises(TypeError):
            giza.libgiza.typed_dict.TypedDict({})

        with self.assertRaises(TypeError):
            giza.libgiza.typed_dict.TypedDict("1", 2, {})

        with self.assertRaises(TypeError):
            giza.libgiza.typed_dict.TypedDict(bool, 2, {})

        with self.assertRaises(TypeError):
            giza.libgiza.typed_dict.TypedDict(2, bool, {})

    def test_check_persistence_of_values_set_after_creation(self):
        d = giza.libgiza.typed_dict.TypedDict(basestring, bool)
        d["foo"] = True
        self.assertEquals(True, d["foo"])

    def test_abc_implementations_return_correctly_typed_values(self):
        d = giza.libgiza.typed_dict.TypedDict(basestring, bool)

        self.assertIsInstance(d.check_key("foo"), giza.libgiza.error.ErrorCollector)
        self.assertIsInstance(d.check_value(True), giza.libgiza.error.ErrorCollector)
        self.assertIsInstance(d.check_pair("foo", True), giza.libgiza.error.ErrorCollector)

    def test_creation_of_objects_works_correctly_with_input_base_object(self):
        for base in [{"foo": True, "bar": False}, [("foo", True), ("bar", False)],
                     {"baz": False}, [("baz", False)], {}, [], tuple()]:
            d = giza.libgiza.typed_dict.TypedDict(basestring, bool)
            d.ingest(base)
            self.assertTrue(len(d) == len(base))


class Fake(object):
    def __init__(self, left, right):
        self.value = (left, right)
        self.validate_results = giza.libgiza.error.ErrorCollector()

    def validate(self):
        return self.validate_results


class FakeTypedDict(giza.libgiza.typed_dict.TypedDict):
    def __init__(self, *args):
        super(FakeTypedDict, self).__init__(key_type=Fake,
                                            value_type=Fake)
        self.ingest(args)
        self.pair_results = giza.libgiza.error.ErrorCollector()

    def check_key(self, key):
        collector = key.validate()
        if collector.has_errors() and collector.fatal:
            raise ValueError("key {0} has an error".format(key))

        return collector

    def check_value(self, value):
        collector = value.validate()
        if collector.has_errors() and collector.fatal:
            raise ValueError
        else:
            return collector

    def check_pair(self, key, value):
        if self.pair_results.has_errors() and self.pair_results.fatal:
            raise ValueError
        else:
            return self.pair_results


class TestTypedDictionaryOperations(unittest.TestCase):
    def setUp(self):
        self.d = FakeTypedDict()
        self.key = Fake(1, 2)
        self.value = Fake(2, 3)

    def test_fake_object_exists_with_correct_types(self):
        self.assertIsInstance(self.d, FakeTypedDict)
        self.assertIsInstance(self.d, giza.libgiza.typed_dict.TypedDict)
        self.assertIsInstance(self.d, dict)

    def test_setting_object_invalid_types_raises_type_errors(self):
        self.assertTrue(len(self.d) == 0)

        pairs = [
            (1, 1),
            (True, False),
            (1, True),
            (False, 0),
            (None, True),
            (False, None),
            ("string value", 3),
            (4, "string value"),
            (Fake(1, 2), 3),
            (Fake(2, 3), "3"),
            (Fake(4, 5), True),
            (3, Fake(5, 6)),
            ("4", Fake(6, 7)),
            (None, Fake(7, 8))
        ]

        for k, v in pairs:
            with self.assertRaises(TypeError):
                self.d[k] = v

        self.assertTrue(len(self.d) == 0)

    def test_setting_object_valid_data_allows_recall(self):
        self.d[self.key] = self.value

        self.assertIs(self.value, self.d[self.key])
        self.assertTrue(len(self.d) == 1)

    def test_setting_object_with_invalid_key_raises_value_error(self):
        self.key.validate_results.add(giza.libgiza.error.Error(message="key has an error"))

        with self.assertRaises(ValueError):
            self.d[self.key] = self.value

    def test_setting_object_with_invalid_value_raises_value_error(self):
        self.key.validate_results.add(giza.libgiza.error.Error(message="value has an error"))

        with self.assertRaises(ValueError):
            self.d[self.key] = self.value

    def test_setting_object_with_invalid_value_and_key_raises_value_error(self):
        self.key.validate_results.add(giza.libgiza.error.Error(message="key has an error"))
        self.key.validate_results.add(giza.libgiza.error.Error(message="value has an error"))

        with self.assertRaises(ValueError):
            self.d[self.key] = self.value

    def test_setting_with_invalid_pair_raises_value_error(self):
        self.key.validate_results.add(giza.libgiza.error.Error(message="an object has errors"))

        with self.assertRaises(ValueError):
            self.d[self.key] = self.value

    def test_abc_implementations_of_checks_return_correctly_typed_values(self):
        self.assertIsInstance(self.d.check_key(self.key), giza.libgiza.error.ErrorCollector)
        self.assertIsInstance(self.d.check_value(self.value), giza.libgiza.error.ErrorCollector)
        self.assertIsInstance(self.d.check_pair(self.key, self.value),
                              giza.libgiza.error.ErrorCollector)

    def test_check_functions_raise_exception(self):
        def bad_pair_validator(self, key, value):
            raise AttributeError("error")

        self.d.check_pair = bad_pair_validator

        with self.assertRaises(ValueError):
            self.d[self.key] = self.value


class LatestReleaseDownloads(giza.libgiza.typed_dict.TypedDict):
    def __init__(self, *args):
        super(LatestReleaseDownloads, self).__init__(key_type=basestring,
                                                     value_type=basestring)
        self.ingest(args)

    def check_key(self, key):
        return giza.libgiza.error.ErrorCollector()

    def check_value(self, value):
        errors = giza.libgiza.error.ErrorCollector()

        if "win" in value:
            if not value.endswith(".zip"):
                errors.add(giza.libgiza.error.Error(
                    message="windows binaries must end with .zip, not: " + value))
        else:
            if not value.endswith(".tgz"):
                errors.add(giza.libgiza.error.Error(
                    message="unix-like packages should end with .tgz: " + value))

        return errors

    def check_pair(self, key, value):
        errors = giza.libgiza.error.ErrorCollector()

        if key.replace("_", "-", 1) not in value:
            errors.add(giza.libgiza.error.ErrorCollector(
                message="key '{0}' is not in value '{1}'".format(key, value)))

        return errors


class LatestReleaseDict(giza.libgiza.typed_dict.TypedDict):
    def __init__(self, *args):
        super(LatestReleaseDict, self).__init__(key_type=basestring,
                                                value_type=LatestReleaseDocument)
        self.ingest(args)

    def check_key(self, key):
        return None

    def check_value(self, value):
        return value.validate()

    def check_pair(self, key, value):
        return None


class LatestReleaseDocument(giza.libgiza.config.ConfigurationBase):
    _option_registry = ["major", "minor", "maintenance"]

    @property
    def version(self):
        return self.state["version"]

    @version.setter
    def version(self, value):
        self.state["version"] = value

    @property
    def date(self):
        return self.state["date"]

    @date.setter
    def date(self, value):
        date_format = "%m/%d/%Y"
        if isinstance(value, datetime.datetime):
            self.state["date"] = value.strftime(date_format)
        elif isinstance(value, basestring):
            # pass through a datetime time object to make sure its valid and
            # well formed.
            self.state["date"] = datetime.datetime.strptime(value,
                                                            date_format).strftime(date_format)
        else:
            raise TypeError("invalid date value: {0}".format(value))

    @property
    def rc(self):
        if "rc" not in self.state:
            return False
        else:
            return self.state["rc"]

    @rc.setter
    def rc(self, value):
        if isinstance(value, bool):
            self.state["rc"] = value
        else:
            raise TypeError("{0} is not a valid 'rc' value".format(value))

    @property
    def downloads(self):
        if "downloads" not in self.state:
            self.state["downloads"] = LatestReleaseDownloads()

        return self.state["downloads"]

    @downloads.setter
    def downloads(self, value):
        self.state["downloads"] = LatestReleaseDownloads(value)

    def validate(self):
        errors = giza.libgiza.error.ErrorCollector()

        for key in ("rc", "version", "major", "minor", "maintenance", "date", "downloads"):
            if key not in self.state:
                m = ("missing {0} in latest release for series {1} "
                     "object".format(key, self.version))
                errors.add(giza.libgiza.error.Error(message=m, include_trace=False))

        for platform, url in self.downloads.items():
            errors.add(self.downloads.check_pair(platform, url))
            errors.add(self.downloads.check_key(platform))
            errors.add(self.downloads.check_value(url))

            if self.version not in url:
                m = ("incorrect version ({0}) for url "
                     "{1}".format(self.version.string, url))
                errors.add(giza.libgiza.error.Error(message=m, include_trace=False))

        return errors


class TestLatestReleaseTypedDict(unittest.TestCase):
    def setUp(self):
        self.d = LatestReleaseDict()
        self.value = LatestReleaseDocument()
        self.value.version = "2.2.2"
        self.value.major = 2
        self.value.minor = 2
        self.value.maintenance = 2
        self.value.rc = False
        self.value.date = "1/16/2014"
        self.value.downloads = {"foo": "https://fastdl.mongodb.org/foo/mongodb-2.2.2-foo.tgz"}

    def test_adding_version(self):
        self.d["2.2"] = self.value
        self.assertIs(self.value, self.d["2.2"])

    def test_creation_from_existing_object(self):
        self.d["2.2"] = self.value

        o = LatestReleaseDict(self.d)
        self.assertEquals(o["2.2"], self.d["2.2"])

    def test_adding_version_with_missing_value(self):
        del self.value.state["date"]

        with self.assertRaises(ValueError):
            self.d["2.2"] = self.value
