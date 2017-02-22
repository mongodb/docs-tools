"""
Unittests of error tracker and collectors. These objects provide a way to track
errors during validation processes, without raising expections until the end of
an aggregated process, without throwing away information about the error itself.
"""
import sys
import unittest
import multiprocessing
import threading

import giza.libgiza.error

if sys.version_info >= (3, 0):
    basestring = str


class TestErrorConstruction(unittest.TestCase):
    def test_create_without_arguments_have_expected_values(self):
        error = giza.libgiza.error.Error()

        self.assertIsNone(error._payload)
        self.assertEquals({}, error.payload)

        self.assertTrue(error.fatal)
        self.assertTrue(error.include_trace)
        self.assertEquals("generic error", error.message)

    def test_create_with_positional_arguments_have_values_that_persist(self):
        msg = "a new message"
        error = giza.libgiza.error.Error(msg, False, False)

        self.assertIsNone(error._payload)
        self.assertEquals({}, error.payload)

        self.assertFalse(error.fatal)
        self.assertFalse(error.include_trace)
        self.assertEquals(msg, error.message)

    def test_create_with_keyword_arguments_have_values_that_persist(self):
        msg = "a new message"
        error = giza.libgiza.error.Error(message=msg, include_trace=False, fatal=False)

        self.assertIsNone(error._payload)
        self.assertEquals({}, error.payload)

        self.assertFalse(error.fatal)
        self.assertFalse(error.include_trace)
        self.assertEquals(msg, error.message)


class TestErrorObject(unittest.TestCase):
    def setUp(self):
        self.error = giza.libgiza.error.Error()

    def test_message_setter_only_accepts_strings_and_raises_type_error_otherwise(self):
        self.assertEquals("generic error", self.error.message)

        for value in [1.02, True, False, None, 42, {"a": 1}, (1, 2), [True, False], {}, []]:
            with self.assertRaises(TypeError):
                self.error.message = value
            self.assertEquals("generic error", self.error.message)

    def test_message_setter_raises_value_error_after_setting_once(self):
        self.assertEquals("generic error", self.error.message)

        self.error.message = "foo"
        self.assertEquals("foo", self.error.message)

        with self.assertRaises(ValueError):
            self.error.message = "bar"

    def test_fatal_setter_returns_true_value_by_default(self):
        self.assertTrue(self.error.fatal)
        del self.error._fatal
        self.assertFalse(hasattr(self.error, "_fatal"))
        self.assertTrue(self.error.fatal)

    def test_fatal_setter_persists_bool_values(self):
        self.assertTrue(self.error.fatal)
        del self.error._fatal
        self.assertFalse(hasattr(self.error, "_fatal"))

        self.error.fatal = False
        self.assertFalse(self.error.fatal)
        self.error.fatal = True
        self.assertTrue(self.error.fatal)
        self.assertTrue(hasattr(self.error, "_fatal"))

    def test_fatal_setter_raises_type_error_when_setting_to_non_boolean(self):
        for value in [1.02, "true", "false", "t", "f", "other string",
                      42, {"a": 1}, (1, 2), [True, False], {}, []]:
            with self.assertRaises(TypeError):
                self.error.fatal = value

    def test_include_trace_setter_returns_true_value_by_default(self):
        self.assertTrue(self.error.include_trace)
        del self.error._include_trace
        self.assertFalse(hasattr(self.error, "_include_trace"))
        self.assertTrue(self.error.include_trace)

    def test_include_trace_setter_raises_type_error_when_setting_to_non_boolean(self):
        for value in [1.02, "true", "false", "t", "f", "other string",
                      42, {"a": 1}, (1, 2), [True, False], {}, []]:
            with self.assertRaises(TypeError):
                self.error.include_trace = value

    def test_include_trace_setter_persists_bool_values(self):
        self.assertTrue(self.error.include_trace)
        del self.error._include_trace
        self.assertFalse(hasattr(self.error, "_include_trace"))

        self.error.include_trace = False
        self.assertFalse(self.error.include_trace)
        self.error.include_trace = True
        self.assertTrue(self.error.include_trace)
        self.assertTrue(hasattr(self.error, "_include_trace"))

    def test_payload_attribute_always_returns_dict(self):
        self.assertIsInstance(self.error.payload, dict)
        self.assertIsNone(self.error._payload)
        self.assertEquals(0, len(self.error.payload))

        conf = giza.libgiza.config.ConfigurationBase()
        conf._option_registry = ["a"]
        conf.a = 1

        for obj in [{"a": 1}, {1: True}, {}, conf,
                    giza.libgiza.config.ConfigurationBase()]:
            self.error.payload = obj
            self.assertIs(obj, self.error._payload)
            self.assertIsInstance(self.error.payload, dict)
            if isinstance(obj, giza.libgiza.config.ConfigurationBase):
                self.assertEquals(len(obj.state), len(self.error.payload))
            else:
                self.assertEquals(len(obj), len(self.error.payload))

    def test_paylod_setter_raises_type_error_when_setting_incorret_type(self):
        for value in [1.02, "true", "false", "t", "f", "other string",
                      42, (1, 2), [True, False], []]:
            with self.assertRaises(TypeError):
                self.error.payload = value

    def test_render_output_returns_string(self):
        output = self.error.render_output()
        self.assertTrue(len(output) > 1)
        self.assertIsInstance(output, basestring)

    def test_render_output_always_prefixes_value(self):
        for prefix in [" ", "   ", "   ", "--", "---", "--->"]:
            output = self.error.render_output(prefix=prefix)
            for ln in output.split("\n"):
                if ln == "":
                    continue

                self.assertTrue(ln.startswith(prefix))

    def test_dict_struct_contains_correct_keys_and_types(self):
        obj = self.error.dict()
        for key in ("message", "payload", "fatal", "trace"):
            self.assertTrue(key in obj)

        self.assertIsInstance(obj["message"], basestring)
        self.assertIsInstance(obj["payload"], dict)
        self.assertIsInstance(obj["fatal"], bool)
        self.assertIsInstance(obj["trace"], list)
        for trace in obj['trace']:
            self.assertIsInstance(trace, dict)
            for key in ("file", "line", "function", "operation"):
                self.assertTrue(key in trace)
                if key == "line":
                    self.assertIsInstance(trace[key], int)
                elif trace[key] is None:
                    # for pypy, the output of traceback is different.
                    continue
                else:
                    self.assertIsInstance(trace[key], basestring)


class CollectorChecks(object):
    def test_emtpy_object_reports_does_not_has_errors(self):
        self.assertFalse(self.collector.fatal)
        self.assertFalse(self.collector.has_errors())

    def test_add_error_modifies_state_of_error_collector(self):
        err = giza.libgiza.error.Error()
        self.assertFalse(self.collector.has_errors())
        self.collector.add(err)
        self.assertTrue(self.collector.has_errors())
        self.assertTrue(self.collector.fatal)
        self.assertTrue(1, len(self.collector))

    def test_add_error_method_raises_type_error_for_invalid_error_types(self):
        for value in [1.02, True, False, 42, {"a": 1}, (1, 2),
                      object(), Exception(), self, TypeError, [True, False], {}, []]:
            with self.assertRaises(TypeError):
                self.collector.add(value)

    def test_add_collector_to_collector_causes_second_collector_to_be_absorbed(self):
        self.assertFalse(self.collector.has_errors())
        sub_collector = giza.libgiza.error.ErrorCollector()
        for _ in range(3):
            self.collector.add(giza.libgiza.error.Error())
            sub_collector.add(giza.libgiza.error.Error())

        self.assertTrue(self.collector.has_errors())
        self.assertEquals(3, len(self.collector))
        self.assertTrue(self.collector.has_errors())
        self.assertEquals(3, len(sub_collector))

        self.collector.add(sub_collector)
        self.assertTrue(self.collector.has_errors())
        self.assertEquals(6, len(self.collector))
        self.assertFalse(sub_collector.has_errors())

    def test_collector_with_non_fatal_errors_render_output_returns_string(self):
        for _ in range(3):
            self.collector.add(giza.libgiza.error.Error(fatal=False))

        output = self.collector.render_output()
        self.assertTrue(len(output) > 1)
        self.assertIsInstance(output, basestring)

    def test_collector_with_fatal_errors_render_output_returns_string(self):
        for _ in range(3):
            self.collector.add(giza.libgiza.error.Error(fatal=True))

        output = self.collector.render_output()
        self.assertTrue(len(output) > 1)
        self.assertIsInstance(output, basestring)
        self.assertTrue("(fatal)" in output)

    def test_render_output_always_prefixes_value(self):
        for _ in range(3):
            self.collector.add(giza.libgiza.error.Error())

        for prefix in [" ", "   ", "   ", "--", "---", "--->"]:
            output = self.collector.render_output(prefix=prefix)
            for ln in output.split("\n"):
                if ln == "":
                    continue

                self.assertTrue(ln.startswith(prefix))

    def test_collector_render_string_returns_emtpy_string_without_errors(self):
        self.assertFalse(self.collector.has_errors())
        self.assertEquals("", self.collector.render_output())

    def test_dict_output_from_empty_collector_is_well_typed(self):
        empty_output = self.collector.dict()
        self.assertTrue("errors" in empty_output)
        self.assertIsInstance(empty_output["errors"], list)
        self.assertEquals(0, len(empty_output["errors"]))

    def test_dict_output_from_collector_is_well_typed(self):
        for _ in range(3):
            self.collector.add(giza.libgiza.error.Error(fatal=True))

        output = self.collector.dict()
        self.assertTrue("errors" in output)
        self.assertIsInstance(output["errors"], list)
        self.assertEquals(3, len(output["errors"]))
        for error in output["errors"]:
            self.assertIsInstance(error, dict)

            for key in ("message", "payload", "fatal", "trace"):
                self.assertTrue(key in error)

            self.assertIsInstance(error["message"], basestring)
            self.assertIsInstance(error["payload"], dict)
            self.assertIsInstance(error["fatal"], bool)
            self.assertIsInstance(error["trace"], list)

            for trace in error['trace']:
                self.assertIsInstance(trace, dict)
                for key in ("file", "line", "function", "operation"):
                    self.assertTrue(key in trace)
                    if key == "line":
                        self.assertIsInstance(trace[key], int)
                    elif trace[key] is None:
                        # for pypy, the output of traceback is different.
                        continue
                    else:
                        self.assertIsInstance(trace[key], basestring)


class TestErrorCollectorProcessLock(CollectorChecks, unittest.TestCase):
    def setUp(self):
        self.collector = giza.libgiza.error.ErrorCollector(name="process-collector",
                                                           concurrency_type="process")

    def test_collector_reports_expected_name(self):
        self.assertEquals("process-collector", self.collector.name)

    def test_collector_lock_uses_correct_type(self):
        self.assertEquals(type(self.collector.lock), type(multiprocessing.RLock()))


class TestErrorCollectorThreadLock(CollectorChecks, unittest.TestCase):
    def setUp(self):
        self.collector = giza.libgiza.error.ErrorCollector(name="thread-collector",
                                                           concurrency_type="thread")

    def test_collector_reports_expected_name(self):
        self.assertEquals("thread-collector", self.collector.name)

    def test_collector_lock_uses_correct_type(self):
        self.assertEquals(type(self.collector.lock), type(threading.RLock()))


class TestErrorCollector(unittest.TestCase):
    def setUp(self):
        self.collector = giza.libgiza.error.ErrorCollector()

    def test_default_name_behavior(self):
        self.assertTrue(hasattr(self.collector, "_name"))
        self.assertEquals("error-collector", self.collector.name)

        del self.collector._name
        self.assertFalse(hasattr(self.collector, "_name"))
        self.assertEquals("error-collector", self.collector.name)

    def test_name_setter_raises_type_error_for_non_string_values(self):
        for value in [1.02, True, False, None, 42, {"a": 1}, (1, 2), [True, False], {}, []]:
            with self.assertRaises(TypeError):
                self.collector.name = value
