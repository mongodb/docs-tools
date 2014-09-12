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

from giza.core.app import BuildApp
from giza.core.pool import ThreadPool, ProcessPool, SerialPool
from giza.core.task import Task
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
        self.app.pool = None
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, ProcessPool)

    def test_pool_setter_process(self):
        self.assertIsNone(self.app.worker_pool)
        a = self.app.pool = 'process'
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, ProcessPool)

    def test_pool_setter_thread(self):
        self.assertIsNone(self.app.worker_pool)
        a = self.app.pool = 'thread'
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, ThreadPool)

    def test_pool_setter_serial(self):
        self.assertIsNone(self.app.worker_pool)
        a = self.app.pool = 'serial'
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, SerialPool)

    def test_pool_setter_process_by_ref(self):
        self.assertIsNone(self.app.worker_pool)
        a = self.app.pool = ProcessPool
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, ProcessPool)

    def test_pool_setter_thread_by_ref(self):
        self.assertIsNone(self.app.worker_pool)
        self.app.pool = ThreadPool
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, ThreadPool)

    def test_pool_setter_serial_by_ref(self):
        self.assertIsNone(self.app.worker_pool)
        self.app.pool = SerialPool
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, SerialPool)

    def test_pool_setter_invalid_input(self):
        self.assertIsNone(self.app.worker_pool)
        a = self.app.pool = 1
        self.assertIsInstance(self.app.pool, ProcessPool)

    def test_pool_closer(self):
        self.assertIsNone(self.app.worker_pool)
        self.app.pool = 'thread'
        self.assertIsInstance(self.app.pool, ThreadPool)
        self.app.close_pool()
        self.assertIsNone(self.app.worker_pool)

    def test_pool_type_checker_thread(self):
        self.assertTrue(self.app.is_pool_type('thread'))

    def test_pool_type_checker_process(self):
        self.assertTrue(self.app.is_pool_type('process'))

    def test_pool_type_checker_serial(self):
        self.assertTrue(self.app.is_pool_type('serial'))

    def test_pool_type_checker_serial_invalid(self):
        self.assertFalse(self.app.is_pool_type('serialized'))

    def test_pool_type_checker_process_invalid(self):
        self.assertFalse(self.app.is_pool_type('proc'))

    def test_pool_type_checker_thread_invalid(self):
        self.assertFalse(self.app.is_pool_type('threaded'))

    def test_is_pool_predicate_serial(self):
        self.assertTrue(self.app.is_pool(SerialPool()))

    def test_add_invalid_object(self):
        with self.assertRaises(TypeError):
            self.app.add(1)

    def test_run_invalid_task(self):
        self.app.queue.append(1)
        with self.assertRaises(TypeError):
            self.app.run()

    def test_single_runner_task(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        t = Task()
        t.job = sum
        t.args = [[ 1 , 2 ], 0]

        self.app._run_single(t)
        self.assertEqual(self.app.results[0], 3)

    def test_single_runner_task_integrated(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        t = self.app.add('task')

        t.job = sum
        t.args = [[ 1 , 2 ], 0]

        self.app.run()

        self.assertEqual(self.app.results[0], 3)

    def test_single_runner_app_integrated(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        app = self.app.add('app')

        t = app.add('task')
        t.job = sum
        t.args = [[ 1 , 2 ], 0]

        self.app.run()
        self.assertEqual(self.app.results[0], 3)

    def test_results_ordering(self):
        expected_results = [12, 13, 14, 15, 7, 17, 18, 10, 20, 12]

        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        for inc in range(10):
            t = self.app.add('task')
            t.job = sum
            if inc in (4, 7, 9):
                t.args = [[ 1 , 2, inc ], 0]
            else:
                t.args = [[ 20 , 2, inc - 10 ], 0]

        self.app.run()

        self.assertEqual(self.app.results,  expected_results)

    def test_single_runner_app_integrated_with_many_subtasks(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        app = self.app.add('app')

        for _ in range(10):
            t = app.add('task')
            t.job = sum
            t.args = [[ 1 , 2 ], 0]

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

    def test_has_apps_predicate_all_apps(self):
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
            self.app.add('app')

        self.assertEqual(len(self.app.queue), 20)
        self.assertTrue(self.app.queue_has_apps)

    def test_running_mixed_queue_all_apps_integrated(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        self.app.pool = 'serial'

        for _ in range(10):
            app = self.app.add('app')
            for _ in range(10):
                t = app.add('task')
                t.job = sum
                t.args = [[1,2], 0]


        self.app.run()

        self.assertEqual(len(self.app.queue), 0)
        self.assertEqual(sum(self.app.results), 300)

    def test_running_mixed_queue_mixed_queue_integrated(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        self.app.pool = 'serial'

        for _ in range(10):
            t = self.app.add('task')
            t.job = sum
            t.args = [[1,2], 0]

        for _ in range(10):
            app = self.app.add('app')
            for _ in range(10):
                t = app.add('task')
                t.job = sum
                t.args = [[1,2], 0]

        self.app.run()

        self.assertEqual(len(self.app.queue), 0)
        self.assertEqual(sum(self.app.results), 330)

    def test_running_mixed_queue_all_apps_direct(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        self.app.pool = 'serial'

        for _ in range(10):
            app = self.app.add('app')
            for _ in range(10):
                t = app.add('task')
                t.job = sum
                t.args = [[1,2], 0]


        self.app._run_mixed_queue()

        self.assertEqual(sum(self.app.results), 300)
        self.assertEqual(len(self.app.queue), 10)

    def test_running_mixed_queue_mixed_queue_direct(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        self.app.pool = 'serial'

        for _ in range(10):
            t = self.app.add('task')
            t.job = sum
            t.args = [[1,2], 0]

        for _ in range(10):
            app = self.app.add('app')
            for _ in range(10):
                t = app.add('task')
                t.job = sum
                t.args = [[1,2], 0]

        self.app._run_mixed_queue()

        self.assertEqual(len(self.app.queue), 20)
        self.assertEqual(sum(self.app.results), 330)

    def test_running_tasks_ordering_serial(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        self.app.pool = 'serial'

        for _ in range(5):
            t = self.app.add('task')
            t.job = sum
            t.args = [[1,2], 0]

        for _ in range(5):
            t = self.app.add('task')
            t.job = sum
            t.args = [[2,2], 0]


        self.app.run()

        self.assertEqual(len(self.app.queue), 0)
        self.assertEqual(self.app.results, [ 3, 3, 3, 3, 3, 4, 4, 4, 4, 4 ])

    def test_task_results_ordering_with_apps(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        for _ in range(3):
            app = self.app.add('app')
            for _ in range(5):
                t = app.add('task')
                t.job = sum
                t.args = [[1,2], 0]
            for _ in range(5):
                t = app.add('task')
                t.job = sum
                t.args = [[2,2], 0]

        self.app.run()

        self.assertEqual(self.app.results,
                         [
                             3, 3, 3, 3, 3, 4, 4, 4, 4, 4,
                             3, 3, 3, 3, 3, 4, 4, 4, 4, 4,
                             3, 3, 3, 3, 3, 4, 4, 4, 4, 4
                         ])

    def test_task_results_ordering_varried_with_apps(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        app = self.app.add('app')
        t = app.add('task')
        t.job = sum
        t.args = [[1, 8], 0]

        for _ in range(3):
            app = self.app.add('app')
            for _ in range(5):
                t = app.add('task')
                t.job = sum
                t.args = [[1,2], 0]

            for _ in range(5):
                t = app.add('task')
                t.job = sum
                t.args = [[2,2], 0]

        app = self.app.add('app')
        t = app.add('task')
        t.job = sum
        t.args = [[2, 8], 0]

        for _ in range(5):
            t = app.add('task')
            t.job = sum
            t.args = [[2,2], 0]

        self.app.run()

        self.assertEqual(self.app.results,
                         [   9,
                             3, 3, 3, 3, 3, 4, 4, 4, 4, 4,
                             3, 3, 3, 3, 3, 4, 4, 4, 4, 4,
                             3, 3, 3, 3, 3, 4, 4, 4, 4, 4,
                             10, 4, 4, 4, 4, 4
                         ])

    def test_task_results_lack_of_order(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        for _ in range(5):
            t = self.app.add('task')
            t.job = sum
            t.args = [[1,2], 0]
        for _ in range(5):
            t = self.app.add('task')
            t.job = sum
            t.args = [[2,2], 0]

        self.app.run()

        # there's a small chance that this could randomly fail without
        # indicating a correctness bug.
        self.assertNotEqual(self.app.results,
                            [
                                3, 3, 3, 3, 3, 4, 4, 4, 4, 4,
                                3, 3, 3, 3, 3, 4, 4, 4, 4, 4,
                                3, 3, 3, 3, 3, 4, 4, 4, 4, 4
                            ])


    def test_task_results_task_and_apps0(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        for _ in range(6):
            t = self.app.add('task')
            t.job = sum
            t.args = [[1,1], 0]

        for _ in range(3):
            app0 = self.app.add('app')
            for _ in range(5):
                t = app0.add('task')
                t.job = sum
                t.args = [[1,2], 0]

            t = self.app.add('task')
            t.job = sum
            t.args = [[1,1], 0]

            app1 = self.app.add('app')
            for _ in range(5):
                t = app1.add('task')
                t.job = sum
                t.args = [[2,2], 0]

        for _ in range(10):
            t = self.app.add('task')
            t.job = sum
            t.args = [[1,1], 0]

        self.app.run()

        print(self.app.results)
        self.assertEqual(self.app.results,
                            [
                                2, 2, 2, 2, 2, 2,
                                3, 3, 3, 3, 3, 2, 4, 4, 4, 4, 4,
                                3, 3, 3, 3, 3, 2, 4, 4, 4, 4, 4,
                                3, 3, 3, 3, 3, 2, 4, 4, 4, 4, 4,
                                2, 2, 2, 2, 2, 2, 2, 2, 2, 2
                            ])

    def test_task_results_task_and_apps1(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        for _ in range(6):
            t = self.app.add('task')
            t.job = sum
            t.args = [[1,1], 0]

        for _ in range(3):
            app = self.app.add('app')
            for _ in range(5):
                t = app.add('task')
                t.job = sum
                t.args = [[1,2], 0]

            t = self.app.add('task')
            t.job = sum
            t.args = [[1,1], 0]

            for _ in range(5):
                t = app.add('task')
                t.job = sum
                t.args = [[2,2], 0]

        for _ in range(10):
            t = self.app.add('task')
            t.job = sum
            t.args = [[1,1], 0]

        self.app.run()

        print(self.app.results)
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
        t = app.add('task')
        t.job = sum
        t.args = [[ 1 , 2 ], 0]

        self.app._run_single(app)
        self.assertEqual(self.app.results[0], 3)

    def test_single_runner_app_with_many_subtasks(self):
        self.assertEqual(self.app.queue, [])
        self.assertEqual(self.app.results, [])

        app = BuildApp()

        for _ in range(10):
            t = app.add('task')
            t.job = sum
            t.args = [[ 1 , 2 ], 0]

        self.app._run_single(app)
        self.assertEqual(len(self.app.results), 10)
        self.assertEqual(self.app.results[0], 3)
        self.assertEqual(sum(self.app.results), 30)

    def test_add_existing_app_object(self):
        self.assertEqual(self.app.queue, [])
        app = BuildApp()
        self.app.add(app)
        self.assertIs(app, self.app.queue[0])
        self.assertIsNot(app, BuildApp())
        self.assertIsNot(BuildApp(), self.app.queue[0])

    def test_add_existing_app_object(self):
        self.assertEqual(self.app.queue, [])
        app = BuildApp(self.c)
        self.app.add(app)
        self.assertIs(app, self.app.queue[0])
        self.assertIsNot(app, BuildApp(self.c))
        self.assertIsNot(BuildApp(self.c), self.app.queue[0])


    def test_pool_setter_existing_pool_thread(self):
        self.assertIsNone(self.app.worker_pool)
        p = ThreadPool(self.c)
        self.app.pool = p
        self.assertIs(self.app.pool, p)

    def test_pool_setter_existing_pool_process(self):
        self.assertIsNone(self.app.worker_pool)
        p = ProcessPool(self.c)
        self.app.pool = p
        self.assertIs(self.app.pool, p)

    def test_pool_setter_existing_pool_serial(self):
        self.assertIsNone(self.app.worker_pool)
        p = SerialPool(self.c)
        self.app.pool = p
        self.assertIs(self.app.pool, p)

    def test_is_pool_predicate_thead(self):
        self.assertTrue(self.app.is_pool(ThreadPool(self.c)))

    def test_is_pool_predicate_process(self):
        self.assertTrue(self.app.is_pool(ProcessPool(self.c)))

    def test_is_pool_predicate_invalid(self):
        self.assertFalse(self.app.is_pool(self.c))
        self.assertFalse(self.app.is_pool(self.app))

class TestBuildAppStandardConfig(CommonAppSuite, TestCase):
    @classmethod
    def setUp(self):
        self.c = Configuration()
        self.c.runstate = RuntimeStateConfig()
        self.app = BuildApp(self.c)

    def test_conf_objet_consistent_in_task(self):
        self.assertEqual(self.app.queue, [])
        t = self.app.add('task')
        self.assertIs(self.c, t.conf)
        self.assertIs(self.c, self.app.queue[0].conf)

    def test_conf_objet_consistent_in_app(self):
        self.assertEqual(self.app.queue, [])
        app = self.app.add('app')
        self.assertIs(self.c, app.conf)
        self.assertIs(self.c, self.app.queue[0].conf)

    def test_conf_objet_consistent_in_new_task(self):
        self.assertEqual(self.app.queue, [])
        t = Task()
        self.assertIsNone(t.conf)
        self.app.add(t)
        self.assertIsNotNone(t.conf)
        self.assertIs(self.c, self.app.queue[0].conf)
        self.assertIs(self.c, t.conf)

class TestBuildAppMinimalConfig(CommonAppSuite, TestCase):
    @classmethod
    def setUp(self):
        self.app = BuildApp()
        self.c = None
