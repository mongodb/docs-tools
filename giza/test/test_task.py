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

from unittest import TestCase

from giza.core.task import MapTask, Task
from giza.config.main import Configuration
from giza.config.runtime import RuntimeStateConfig

class BaseTaskSuite(object):
    def test_configuration_object_validation_rejection(self):
        for i in [None, 1, 'config', {'config': 1}]:
            t = self.Task()

            with self.assertRaises(TypeError):
                t.conf = i

    def test_configuration_object_validation_acceptance(self):
        for i in [self.c, Configuration(), RuntimeStateConfig()]:
            t = self.Task()
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

        self.task.args = { 'foo': 1 }
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
            print(iterable, start)
            return sum(iterable, start)

        for i in (((1,2,3), 0), ([1,2,3], 0), {'iterable': [1,2,3], 'start': 0}):
            t = self.Task()

            t.job = sum_func
            t.args = i
            t.description = "test task: " + str(i)

            self.assertEqual(t.run(), 6)

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
        t.iter = [ (i, i+10) for i in range(10) ]
        t.job = sum

        for a,b in zip(t.run(), [10, 12, 14, 16, 18, 20, 22, 24, 26, 28]):
            self.assertEqual(a,b)
