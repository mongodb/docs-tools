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
import random
from unittest import TestCase

from giza.libgiza.app import BuildApp
from giza.libgiza.pool import ThreadPool, ProcessPool, SerialPool
from giza.libgiza.task import Task
from giza.config.main import Configuration
from giza.config.runtime import RuntimeStateConfig


class CommonAppSuite(object):
    def test_add_make_test_default(self):
        self.assertEqual(self.app.queue, [])
        self.app.add()
        self.assertTrue(len(self.app.queue) == 1)
        self.assertTrue(isinstance(self.app.queue[0], Task))

    def test_add_make_test_task(self):
        self.assertEqual(self.app.queue, [])
        self.app.add('task')
        self.assertTrue(len(self.app.queue) == 1)
        self.assertTrue(isinstance(self.app.queue[0], Task))

    def test_add_make_test_app(self):
        self.assertEqual(self.app.queue, [])
        self.app.add('app')
        self.assertTrue(len(self.app.queue) == 1)
        self.assertIsInstance(self.app.queue[0], BuildApp)

    def test_add_existing_task_object(self):
        self.assertEqual(self.app.queue, [])
        t = Task()
        self.app.add(t)
        self.assertIs(t, self.app.queue[0])
        self.assertIsNot(t, Task())
        self.assertIsNot(Task(), self.app.queue[0])

    def test_pool_setter_default(self):
        self.assertIsNone(self.app.worker_pool)
        pool_type = self.app.default_pool

        if pool_type == 'lazy':
            pool_type = random.choice(['thread', 'serial'])

        self.app.pool = pool_type

        self.assertIsNone(self.app.worker_pool)
        self.app.create_pool()
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, self.app.pool_mapping[pool_type])

    def test_pool_setter_process(self):
        self.assertIsNone(self.app.worker_pool)
        self.app.pool = 'process'
        self.assertIsNone(self.app.worker_pool)
        self.app.create_pool()
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, ProcessPool)
        self.assertTrue(self.app.has_active_pool())

    def test_pool_setter_thread(self):
        self.assertIsNone(self.app.worker_pool)
        self.app.pool = 'thread'
        self.assertIsNone(self.app.worker_pool)
        self.app.create_pool()
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, ThreadPool)
        self.assertTrue(self.app.has_active_pool())

    def test_pool_setter_serial(self):
        self.assertIsNone(self.app.worker_pool)
        self.app.pool = 'serial'
        self.assertIsNone(self.app.worker_pool)
        self.app.create_pool()
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, SerialPool)
        self.assertTrue(self.app.has_active_pool())

    def test_pool_setter_process_by_ref(self):
        self.assertIsNone(self.app.worker_pool)
        self.app.pool = ProcessPool
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, ProcessPool)
        self.assertTrue(self.app.has_active_pool())

    def test_pool_setter_thread_by_ref(self):
        self.assertIsNone(self.app.worker_pool)
        self.app.pool = ThreadPool
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, ThreadPool)
        self.assertTrue(self.app.has_active_pool())

    def test_pool_setter_serial_by_ref(self):
        self.assertIsNone(self.app.worker_pool)
        self.app.pool = SerialPool
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, SerialPool)
        self.assertTrue(self.app.has_active_pool())

    def test_pool_setter_invalid_input(self):
        self.assertIsNone(self.app.worker_pool)
        self.app.default_pool = 'serial'

        self.app.pool = 1
        self.app.create_pool()
        self.assertIn(type(self.app.pool), self.app.pool_mapping.values())
        self.assertTrue(self.app.has_active_pool())

    def test_pool_closer(self):
        self.assertIsNone(self.app.worker_pool)
        self.app.pool = 'thread'
        self.assertIsNone(self.app.worker_pool)
        self.app.create_pool()
        self.assertIsInstance(self.app.pool, ThreadPool)
        self.assertTrue(self.app.has_active_pool())
        self.app.close_pool()
        self.assertIsNone(self.app.worker_pool)
        self.assertFalse(self.app.has_active_pool())

    def test_add_invalid_object(self):
        with self.assertRaises(TypeError):
            self.app.add(1)

    def test_single_runner_task(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        t = Task()
        t.job = sum
        t.description = 'test task'
        t.args = [[1, 2], 0]

        self.app.add(t)
        self.app.run(t)
        self.assertEqual(self.app.results[0], 3)

    def test_single_runner_task_integrated(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        t = self.app.add('task')

        t.job = sum
        t.args = [[1, 2], 0]
        t.description = 'test task'

        self.app.add(t)
        self.app.run()
        self.assertEqual(self.app.results[0], 3)

    def test_single_runner_app_integrated(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        app = self.app.add('app')

        t = app.add('task')
        t.job = sum
        t.description = 'test task'
        t.args = [[1, 2], 0]

        self.app.run()
        self.assertEqual(self.app.results[0], 3)

    def test_results_ordering(self):
        expected_results = [12, 13, 14, 15, 7, 17, 18, 10, 20, 12]

        self.assertIsNone(self.app.pool)
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        for inc in range(10):
            t = self.app.add('task')
            t.job = sum
            if inc in (4, 7, 9):
                t.args = [[1, 2, inc], 0]
            else:
                t.args = [[20, 2, inc - 10], 0]
            t.description = 'test task'

        self.app.run()
        self.assertEqual(self.app.results, expected_results)

    def test_single_runner_app_integrated_with_many_subtasks(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        app = self.app.add('app')

        for _ in range(10):
            t = app.add('task')
            t.job = sum
            t.args = [[1, 2], 0]
            t.description = 'test task'

        self.app.run()
        self.assertEqual(len(self.app.results), 10)
        self.assertEqual(self.app.results[0], 3)
        self.assertEqual(sum(self.app.results), 30)

    def test_has_apps_predicate_single(self):
        self.assertEqual(self.app.queue, [])

        self.app.queue.append(None)
        self.assertFalse(self.app.queue_has_apps)

    def test_has_apps_predicate_empty(self):
        self.assertEqual(self.app.queue, [])
        self.assertFalse(self.app.queue_has_apps)

    def test_has_apps_predicate_all_tasks(self):
        self.assertEqual(self.app.queue, [])

        for _ in range(10):
            self.app.add('task')

        self.assertEqual(len(self.app.queue), 10)
        self.assertFalse(self.app.queue_has_apps)

    def test_has_apps_with_member_tasks_predicate_all_apps(self):
        self.assertEqual(self.app.queue, [])

        for _ in range(10):
            a = self.app.add('app')
            self.assertIsInstance(a, BuildApp)
            t = a.add('task')
            t.job = sum
            t.args = (1, 2)

        self.assertEqual(len(self.app.queue), 10)
        self.assertTrue(self.app.queue_has_apps)

    def test_has_apps_without_member_tasks_predicate_all_apps(self):
        self.assertEqual(self.app.queue, [])

        for _ in range(10):
            self.app.add('app')

        self.assertEqual(len(self.app.queue), 10)
        self.assertTrue(self.app.queue_has_apps)

    def test_has_apps_predicate_mixed(self):
        self.assertEqual(self.app.queue, [])

        for _ in range(10):
            self.app.add('task')

        for _ in range(10):
            a = self.app.add('app')
            self.assertIsInstance(a, BuildApp)
            t = a.add('task')
            t.job = sum
            t.args = (1, 2)

        self.assertTrue(self.app.queue_has_apps)

    def test_running_mixed_queue_all_apps_integrated(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        for _ in range(10):
            app = self.app.add('app')
            for _ in range(10):
                t = app.add('task')
                t.job = sum
                t.args = [[1, 2], 0]
                t.description = 'test task'

        self.app.run()

        self.assertEqual(len(self.app.queue), 0)
        self.assertEqual(sum(self.app.results), 300)

    def test_running_mixed_queue_mixed_queue_integrated(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        for _ in range(10):
            t = self.app.add('task')
            t.job = sum
            t.args = [[1, 2], 0]
            t.description = 'test task'

        for _ in range(10):
            app = self.app.add('app')
            for _ in range(10):
                t = app.add('task')
                t.job = sum
                t.args = [[1, 2], 0]
                t.description = 'test task'

        self.app.run()

        self.assertEqual(len(self.app.queue), 0)
        self.assertEqual(sum(self.app.results), 330)

    def test_running_mixed_queue_all_apps_direct(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        for _ in range(10):
            app = self.app.add('app')
            for _ in range(10):
                t = app.add('task')
                t.job = sum
                t.args = [[1, 2], 0]
                t.description = 'test task'

        self.app.create_pool('thread')
        self.app._run_mixed_queue()

        self.assertEqual(sum(self.app.results), 300)
        self.assertEqual(len(self.app.queue), 10)

    def test_running_mixed_queue_mixed_queue_direct(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        self.app.default_pool = 'thread'
        self.app.create_pool()

        for _ in range(10):
            t = self.app.add('task')
            t.job = sum
            t.args = [[1, 2], 0]
            t.description = 'test task'

        for _ in range(10):
            app = self.app.add('app')
            app.pool = self.app.pool
            for _ in range(10):
                t = app.add('task')
                t.job = sum
                t.args = [[1, 2], 0]
                t.description = 'test task'

        self.app._run_mixed_queue()

        self.assertEqual(len(self.app.queue), 20)
        self.assertEqual(sum(self.app.results), 330)

    def test_running_tasks_ordering_serial(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        for _ in range(5):
            t = self.app.add('task')
            t.job = sum
            t.args = [[1, 2], 0]
            t.description = 'test task'

        for _ in range(5):
            t = self.app.add('task')
            t.job = sum
            t.args = [[2, 2], 0]
            t.description = 'test task'

        self.app.create_pool()
        self.app.run()

        self.assertEqual(len(self.app.queue), 0)
        self.assertEqual(self.app.results, [3, 3, 3, 3, 3, 4, 4, 4, 4, 4])

    def test_task_results_ordering_with_apps(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        for _ in range(3):
            app = self.app.add('app')
            for _ in range(5):
                t = app.add('task')
                t.job = sum
                t.args = [[1, 2], 0]
                t.description = 'test task'

            for _ in range(5):
                t = app.add('task')
                t.job = sum
                t.args = [[2, 2], 0]
                t.description = 'test task'

        self.app.run()

        self.assertEqual(self.app.results,
                         [3, 3, 3, 3, 3, 4, 4, 4, 4, 4,
                          3, 3, 3, 3, 3, 4, 4, 4, 4, 4,
                          3, 3, 3, 3, 3, 4, 4, 4, 4, 4])

    def test_task_results_ordering_varried_with_apps(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        app = self.app.add('app')
        t = app.add('task')
        t.job = sum
        t.args = [[1, 8], 0]
        t.description = 'test task'

        for _ in range(3):
            app = self.app.add('app')
            for _ in range(5):
                t = app.add('task')
                t.job = sum
                t.args = [[1, 2], 0]
                t.description = 'test task'

            for _ in range(5):
                t = app.add('task')
                t.job = sum
                t.args = [[2, 2], 0]
                t.description = 'test task'

        app = self.app.add('app')
        t = app.add('task')
        t.job = sum
        t.args = [[2, 8], 0]

        for _ in range(5):
            t = app.add('task')
            t.job = sum
            t.args = [[2, 2], 0]
            t.description = 'test task'

        self.app.run()

        expected_results = [9,
                            3, 3, 3, 3, 3, 4, 4, 4, 4, 4,
                            3, 3, 3, 3, 3, 4, 4, 4, 4, 4,
                            3, 3, 3, 3, 3, 4, 4, 4, 4, 4,
                            10, 4, 4, 4, 4, 4]

        self.assertEqual(sorted(self.app.results), sorted(expected_results))
        self.assertEqual(self.app.results, expected_results)

    def test_task_results_lack_of_order(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        for _ in range(5):
            t = self.app.add('task')
            t.job = sum
            t.args = [[1, 2], 0]
            t.description = 'test task'

        for _ in range(5):
            t = self.app.add('task')
            t.job = sum
            t.args = [[2, 2], 0]
            t.description = 'test task'

        self.app.run()

        # there's a small chance that this could randomly fail without
        # indicating a correctness bug.
        self.assertNotEqual(self.app.results,
                            [3, 3, 3, 3, 3, 4, 4, 4, 4, 4,
                             3, 3, 3, 3, 3, 4, 4, 4, 4, 4,
                             3, 3, 3, 3, 3, 4, 4, 4, 4, 4])

    def test_task_results_task_and_apps0(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        for _ in range(6):
            t = self.app.add('task')
            t.job = sum
            t.args = [[1, 1], 0]
            t.description = 'test task'

        for _ in range(3):
            app0 = self.app.add('app')
            for _ in range(5):
                t = app0.add('task')
                t.job = sum
                t.args = [[1, 2], 0]
                t.description = 'test task'

            t = self.app.add('task')
            t.job = sum
            t.args = [[1, 1], 0]
            t.description = 'test task'

            app1 = self.app.add('app')
            for _ in range(5):
                t = app1.add('task')
                t.job = sum
                t.args = [[2, 2], 0]
                t.description = 'test task'

        for _ in range(10):
            t = self.app.add('task')
            t.job = sum
            t.args = [[1, 1], 0]
            t.description = 'test task'

        self.app.run()

        self.assertEqual(self.app.results,
                         [2, 2, 2, 2, 2, 2,
                          3, 3, 3, 3, 3, 2, 4, 4, 4, 4, 4,
                          3, 3, 3, 3, 3, 2, 4, 4, 4, 4, 4,
                          3, 3, 3, 3, 3, 2, 4, 4, 4, 4, 4,
                          2, 2, 2, 2, 2, 2, 2, 2, 2, 2])

    def test_task_results_task_and_apps1(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        for _ in range(6):
            t = self.app.add('task')
            t.job = sum
            t.args = [[1, 1], 0]
            t.description = 'test task'

        for _ in range(3):
            app = self.app.add('app')
            for _ in range(5):
                t = app.add('task')
                t.job = sum
                t.args = [[1, 2], 0]
                t.description = 'test task'

            t = self.app.add('task')
            t.job = sum
            t.args = [[1, 1], 0]
            t.description = 'test task'

            for _ in range(5):
                t = app.add('task')
                t.job = sum
                t.args = [[2, 2], 0]
                t.description = 'test task'

        for _ in range(10):
            t = self.app.add('task')
            t.job = sum
            t.args = [[1, 1], 0]
            t.description = 'test task'

        self.app.run()

        self.assertEqual(self.app.results,
                         [2, 2, 2, 2, 2, 2,
                          3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 2,
                          3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 2,
                          3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 2,
                          2, 2, 2, 2, 2, 2, 2, 2, 2, 2
                          ])

    def test_single_runner_app(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        app = BuildApp()
        app.pool_size = 2
        t = app.add('task')
        t.job = sum
        t.args = [[1, 2], 0]
        t.description = 'test task'

        self.app.add(app)
        self.app.run()
        self.assertEqual(self.app.results[0], 3)

    def test_single_runner_app_with_many_subtasks(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        app = BuildApp()
        app.pool_size = 2

        for _ in range(10):
            t = app.add('task')
            t.job = sum
            t.description = 'test task'
            t.args = [[1, 2], 0]

        self.app.add(app)
        self.app.run()
        self.assertEqual(len(self.app.results), 10)
        self.assertEqual(self.app.results[0], 3)
        self.assertEqual(sum(self.app.results), 30)

    def test_add_existing_app_object(self):
        self.assertEqual(self.app.queue, [])
        app = BuildApp()
        app.pool_size = 2
        self.app.add(app)
        self.assertIs(app, self.app.queue[0])
        self.assertIsNot(app, BuildApp())
        self.assertIsNot(BuildApp(), self.app.queue[0])

    def test_pool_setter_existing_pool_thread(self):
        self.assertIsNone(self.app.worker_pool)
        p = ThreadPool(self.c)
        p.pool_size = 2
        self.app.pool = p
        self.assertIs(self.app.pool, p)

    def test_pool_setter_existing_pool_process(self):
        self.assertIsNone(self.app.worker_pool)
        p = ProcessPool(self.c)
        p.pool_size = 2
        self.app.pool = p
        self.assertIs(self.app.pool, p)

    def test_pool_setter_existing_pool_serial(self):
        self.assertIsNone(self.app.worker_pool)
        p = SerialPool(self.c)
        self.app.pool = p
        self.assertIs(self.app.pool, p)

    def test_pool_clenser_removes_empty_apps(self):
        self.assertEqual(len(self.app.queue), 0)

        a = self.app.add('app')
        self.assertIsInstance(a, BuildApp)

        self.assertEqual(len(self.app.queue), 1)
        self.app.clean_queue()
        self.assertEqual(len(self.app.queue), 0)

    def test_finalizers_simple(self):
        t = Task(job=sum,
                 args=((1, 2, 3), 0))

        self.assertEqual(t.finalizers, [])

        t.finalizers = [
            Task(job=sum,
                 args=((4, 5, 6, i), 0))
            for i in range(10)
        ]

        self.app.add(t)
        results = self.app.run()
        self.assertEqual(len(results), 11)
        self.assertEqual(results,
                         [6, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24])

    def test_finalizers_nested(self):
        t = Task(job=sum,
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

        self.app.add(t)
        results = self.app.run()
        self.assertEqual(len(results), 111)
        self.assertEqual(results[0], 6)
        self.assertEqual(results[1], 15)

        for result in results:
            self.assertIsInstance(result, numbers.Number)
            self.assertTrue(result >= 6)
            self.assertTrue(result <= 24)

    def test_dependency(self):
        self.assertIsNone(self.app.dependency)

        test_value = "string"
        self.app.dependency = test_value
        self.assertIsNotNone(self.app.dependency)
        self.assertIs(test_value, self.app.dependency)

    def test_target(self):
        self.assertIsNone(self.app.target)

        test_value = "string"
        self.app.target = test_value
        self.assertIsNotNone(self.app.target)
        self.assertIs(test_value, self.app.target)

    def test_description(self):
        # if no jobs defined.

        sub_app = self.app.add("app")

        self.assertTrue("member" in sub_app.description)
        self.assertTrue("root level" in self.app.description)

        self.assertEquals(0, len(sub_app.queue))
        self.assertTrue(sub_app.description.endswith(": []"))
        self.assertEquals(1, len(self.app.queue))
        self.assertTrue(self.app.description.endswith(": [{0}]".format(type(self.app))))


class TestBuildAppStandardConfig(CommonAppSuite, TestCase):
    def setUp(self):
        self.c = Configuration()
        self.c.runstate = RuntimeStateConfig()
        self.app = BuildApp(self.c)
        self.app.default_pool = random.choice(['serial', 'thread'])
        self.app.pool_size = 2

    def test_conf_object_consistent_in_task(self):
        self.assertEqual(self.app.queue, [])
        t = self.app.add('task')
        self.assertIs(self.c, t.conf)
        self.assertIs(self.c, self.app.queue[0].conf)

    def test_conf_object_consistent_in_app(self):
        self.assertEqual(self.app.queue, [])
        self.app.add('app')

        self.assertIs(self.c, self.app.conf)
        self.assertIs(self.c, self.app.queue[0].conf)

    def test_conf_object_consistent_in_new_task(self):
        self.assertEqual(self.app.queue, [])
        t = Task()
        self.assertIsNone(t.conf)
        self.app.add(t)
        self.assertIsNotNone(t.conf)
        self.assertIs(self.c, self.app.queue[0].conf)
        self.assertIs(self.c, t.conf)

    def test_force_options(self):
        self.assertEquals(self.c.runstate.force, self.app.force)
        self.assertFalse(self.c.runstate.force)
        self.assertFalse(self.app.force)

        self.app._force = None
        self.assertFalse(self.app.force)

    def test_default_pool_size(self):
        self.assertIsNotNone(self.c)
        self.assertIsNotNone(self.app.conf)
        self.app._pool_size = None
        self.assertEquals(self.c.runstate.pool_size, self.app.pool_size)

    def tearDown(self):
        self.app.close_pool()


class TestBuildAppMinimalConfig(CommonAppSuite, TestCase):
    @classmethod
    def setUp(self):
        self.app = BuildApp()
        self.app.default_pool = random.choice(['serial', 'thread'])
        self.app.pool_size = 2
        self.c = None

    def tearDown(self):
        self.app.close_pool()


class TestBuildAppAlternateConstructor(CommonAppSuite, TestCase):
    @classmethod
    def setUp(self):
        self.app = BuildApp.new(pool_type=random.choice(['serial', 'thread']),
                                pool_size=None, force=None)
        self.c = None

    def tearDown(self):
        self.app.close_pool()

    # the following tests aren't specifically relevant to this constructor, but
    # rather to the "None" value of the constructor.

    def test_force_setter(self):
        self.assertIsNone(self.app.conf)
        self.assertFalse(self.app.force)
        self.app._force = None
        self.assertFalse(self.app.force)

    def test_pool_size(self):
        self.assertIsNone(self.app.pool_size)
