# Copyright 2014 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numbers

from unittest import TestCase

from libgiza.task import MapTask, Task
from libgiza.app import BuildApp
from giza.config.main import Configuration
from giza.config.runtime import RuntimeStateConfig


class BaseTaskSuite(object):
    def test_configuration_object_validation_rejection(self):
        for i in [1, 'config', {'config': 1}]:
            t = self.Task()

            with self.assertRaises(TypeError):
                t.conf = i

    def test_configuration_object_validation_acceptance(self):
        for i in [self.c, Configuration(), RuntimeStateConfig()]:
            t = self.Task()

            self.assertIsNone(t.conf)
            t.conf = i
            self.assertIs(i, t.conf)

    def test_job_validation_rejection(self):
        for i in [None, True, False, 1, 'foo']:
            t = self.Task()

            with self.assertRaises(TypeError):
                t.job = i

    def test_job_validation_acceptance(self):
        for i in [Configuration, sum, TypeError, map]:
            t = self.Task()
            t.job = i

            self.assertIs(i, t.job)

    def test_args_type_setting_dict(self):
        self.assertIsNone(self.task._args)
        self.assertIsNone(self.task.args_type)

        self.task.args = {'foo': 1}
        self.assertEqual(self.task.args_type, 'kwargs')

    def test_args_type_setting_args(self):
        self.assertIsNone(self.task._args)
        self.assertIsNone(self.task.args_type)

        self.task.args = [1, 2, 3, 4]
        self.assertEqual(self.task.args_type, 'args')

    def test_args_type_setting_tuple(self):
        self.assertIsNone(self.task._args)
        self.assertIsNone(self.task.args_type)

        self.task.args = (1, 2, 3, 4)
        self.assertEqual(self.task.args_type, 'args')

    def test_args_type_setting_string(self):
        self.assertIsNone(self.task._args)
        self.assertIsNone(self.task.args_type)

        self.task.args = 'None'
        self.assertEqual(self.task.args_type, 'args')

    def test_rebuild_requirment_checker_base(self):
        self.assertIsNone(self.task.target)
        self.assertIsNone(self.task.dependency)
        self.assertFalse(self.c.runstate.force)

        self.assertTrue(self.task.needs_rebuild)

    def test_rebuild_requirment_checker_dep(self):
        self.task.target = True

        self.assertIsNotNone(self.task.target)
        self.assertIsNone(self.task.dependency)
        self.assertFalse(self.c.runstate.force)

        self.assertTrue(self.task.needs_rebuild)

    def test_rebuild_requirment_checker_force(self):
        self.task.target = True
        self.task.dependency = True
        self.c.runstate.force = True

        self.assertIsNotNone(self.task.target)
        self.assertIsNotNone(self.task.dependency)
        self.assertTrue(self.c.runstate.force)

        self.assertTrue(self.task.needs_rebuild)

    def test_finalizer_setter_error_app(self):
        with self.assertRaises(TypeError):
            self.task.finalizers = BuildApp()

    def test_finalizer_setter_error_app_in_list(self):
        with self.assertRaises(TypeError):
            self.task.finalizers = [self.Task(), BuildApp()]

    def test_add_finalizer_returns_task(self):
        self.assertTrue(len(self.task.finalizers) == 0)
        t = self.Task()
        check = self.task.add_finalizer(t)
        self.assertIs(t, check)

    def test_finalizer_setter_error_fallthrough(self):
        with self.assertRaises(TypeError):
            self.task.finalizers = 1

    def test_finalizer_setter_error_nested_list(self):
        with self.assertRaises(TypeError):
            self.task.finalizers = [self.Task(), [self.Task(), self.Task()]]

    def test_finalizer_setter_non_distructive_assignment(self):
        self.assertEqual(len(self.task.finalizers), 0)
        self.task.finalizers = self.Task()
        self.assertEqual(len(self.task.finalizers), 1)
        self.task.finalizers = self.Task()
        self.assertEqual(len(self.task.finalizers), 2)
        self.task.finalizers = [self.Task(), self.Task(), self.Task(), self.Task()]
        self.assertEqual(len(self.task.finalizers), 6)

    def test_finalizer_setter_special_case_for_tuples_error(self):
        self.assertEqual(len(self.task.finalizers), 0)
        with self.assertRaises(TypeError):
            self.task.finalizers = (self.Task(), 'keyword')

    def test_finalizer_setter_special_case_for_tuples_list_error(self):
        self.assertEqual(len(self.task.finalizers), 0)
        with self.assertRaises(TypeError):
            self.task.finalizers = [(self.Task(), 'keyword'), self.Task()]

    def test_finalizer_setter_special_case_for_tuples(self):
        self.assertEqual(len(self.task.finalizers), 0)
        self.task.finalizers = ('keyword', self.Task())
        self.assertEqual(len(self.task.finalizers), 1)

    def test_finalizer_setter_special_case_for_tuples_list(self):
        self.assertEqual(len(self.task.finalizers), 0)
        self.task.finalizers = [('keyword', self.Task()), self.Task()]
        self.assertEqual(len(self.task.finalizers), 2)


class TestTask(BaseTaskSuite, TestCase):
    @classmethod
    def setUp(self):
        self.c = Configuration()
        self.c.runstate = RuntimeStateConfig()
        self.task = Task()
        self.task.job = sum
        self.Task = Task
        self.task.conf = self.c

    def test_running_tasks(self):
        def sum_func(iterable, start):
            return sum(iterable, start)

        for i in (((1, 2, 3), 0), ([1, 2, 3], 0), {'iterable': [1, 2, 3], 'start': 0}):
            t = self.Task()

            t.job = sum_func
            t.args = i
            t.description = "test task: " + str(i)

            self.assertEqual(t.run(), 6)

    def test_finalizers_simple(self):
        t = self.Task(job=sum,
                      args=((1, 2, 3), 0))

        self.assertEqual(t.finalizers, [])

        t.finalizers = [
            Task(job=sum,
                 args=((4, 5, 6, i), 0))
            for i in range(10)
        ]

        self.assertEqual(len(t.finalizers), 10)
        self.assertEqual(t.run(), 6)
        self.assertEqual(len(t.finalizers), 10)
        finals = t.finalize()
        self.assertEqual(len(finals), 10)
        self.assertEqual(len(t.finalizers), 10)
        self.assertEqual(finals,
                         [15, 16, 17, 18, 19, 20, 21, 22, 23, 24])

    def test_finalizers_nested(self):
        t = self.Task(job=sum,
                      args=((1, 2, 3), 0))

        self.assertEqual(t.finalizers, [])

        t.finalizers = [
            Task(job=sum,
                 args=((4, 5, 6, i), 0))
            for i in range(10)
        ]
        self.assertEqual(len(t.finalizers), 10)

        for task in t.finalizers:
            task.finalizers.extend([
                Task(job=sum,
                     args=((4, 5, 6, i), 0))
                for i in range(10)
            ])
            self.assertEqual(len(task.finalizers), 10)

        task_result = t.run()
        self.assertEqual(task_result, 6)
        results = [task_result]
        results.extend(t.finalize())

        self.assertEqual(len(results), 111)
        self.assertEqual(results[0], 6)
        self.assertEqual(results[1], 15)

        for result in results:
            self.assertIsInstance(result, numbers.Number)
            self.assertTrue(result >= 6)
            self.assertTrue(result <= 24)


class TestMapTask(BaseTaskSuite, TestCase):
    @classmethod
    def setUp(self):
        self.c = Configuration()
        self.c.runstate = RuntimeStateConfig()
        self.task = MapTask()
        self.task.job = sum
        self.Task = MapTask
        self.task.conf = self.c

    def test_running_map_task(self):
        t = self.Task()
        t.iter = [(i, i+10) for i in range(10)]
        t.job = sum

        for a, b in zip(t.run(), [10, 12, 14, 16, 18, 20, 22, 24, 26, 28]):
            self.assertEqual(a, b)
