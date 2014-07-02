from giza.app import BuildApp
from giza.pool import ThreadPool, ProcessPool, SerialPool
from giza.task import Task
from giza.config.main import Configuration
from giza.config.runtime import RuntimeStateConfig
from unittest import TestCase

class TestBuildApp(TestCase):
    @classmethod
    def setUp(self):
        self.c = Configuration()
        self.c.runstate = RuntimeStateConfig()
        self.app = BuildApp(self.c)

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
        t = Task(self.c)
        self.app.add(t)
        self.assertIs(t, self.app.queue[0])
        self.assertIsNot(t, Task(self.c))
        self.assertIsNot(Task(self.c), self.app.queue[0])

    def test_add_existing_app_object(self):
        self.assertEqual(self.app.queue, [])
        app = BuildApp(self.c)
        self.app.add(app)
        self.assertIs(app, self.app.queue[0])
        self.assertIsNot(app, BuildApp(self.c))
        self.assertIsNot(BuildApp(self.c), self.app.queue[0])

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

    def test_conf_objet_consistent_in_task(self):
        self.assertEqual(self.app.queue, [])
        t = Task()
        self.assertIsNone(t.conf)
        self.app.add(t)
        self.assertIsNotNone(t.conf)
        self.assertIs(self.c, self.app.queue[0].conf)
        self.assertIs(self.c, t.conf)

    def test_pool_setter_default(self):
        self.assertIsNone(self.app._worker_pool)
        a = self.app.pool = None
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, ProcessPool)

    def test_pool_setter_process(self):
        self.assertIsNone(self.app._worker_pool)
        a = self.app.pool = 'process'
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, ProcessPool)

    def test_pool_setter_thread(self):
        self.assertIsNone(self.app._worker_pool)
        a = self.app.pool = 'thread'
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, ThreadPool)

    def test_pool_setter_serial(self):
        self.assertIsNone(self.app._worker_pool)
        a = self.app.pool = 'serial'
        self.assertIsNotNone(self.app.worker_pool)
        self.assertIsInstance(self.app.pool, SerialPool)

    def test_pool_setter_invalid_input(self):
        self.assertIsNone(self.app._worker_pool)
        a = self.app.pool = 1
        self.assertIsInstance(self.app.pool, ProcessPool)

    def test_pool_setter_existing_pool_thread(self):
        self.assertIsNone(self.app._worker_pool)
        p = ThreadPool(self.c)
        self.app.pool = p
        self.assertIs(self.app.pool, p)

    def test_pool_setter_existing_pool_process(self):
        self.assertIsNone(self.app._worker_pool)
        p = ProcessPool(self.c)
        self.app.pool = p
        self.assertIs(self.app.pool, p)

    def test_pool_setter_existing_pool_serial(self):
        self.assertIsNone(self.app._worker_pool)
        p = SerialPool(self.c)
        self.app.pool = p
        self.assertIs(self.app.pool, p)

    def test_pool_closer(self):
        self.assertIsNone(self.app._worker_pool)
        a = self.app.pool = 'thread'
        self.assertIsInstance(self.app.pool, ThreadPool)
        self.app.close_pool()
        self.assertIsNone(self.app._worker_pool)

    def test_pool_type_checker_thread(self):
        self.assertTrue(BuildApp.is_pool_type('thread'))

    def test_pool_type_checker_process(self):
        self.assertTrue(BuildApp.is_pool_type('process'))

    def test_pool_type_checker_serial(self):
        self.assertTrue(BuildApp.is_pool_type('serial'))

    def test_pool_type_checker_serial_invalid(self):
        self.assertFalse(BuildApp.is_pool_type('serialized'))

    def test_pool_type_checker_process_invalid(self):
        self.assertFalse(BuildApp.is_pool_type('proc'))

    def test_pool_type_checker_thread_invalid(self):
        self.assertFalse(BuildApp.is_pool_type('threaded'))

    def test_is_pool_predicate_thead(self):
        self.assertTrue(BuildApp.is_pool(ThreadPool()))

    def test_is_pool_predicate_process(self):
        self.assertTrue(BuildApp.is_pool(ProcessPool()))

    def test_is_pool_predicate_serial(self):
        self.assertTrue(BuildApp.is_pool(SerialPool()))

    def test_is_pool_predicate_invalid(self):
        self.assertFalse(BuildApp.is_pool(self.c))
        self.assertFalse(BuildApp.is_pool(self.app))

    # TODO:
    #  - test exceptions if adding non-task object.
    #  - test adding tasks by passing class ref
    #  - test type error in run, if adding a single non-task object
    #  - test run method, which might require refactoring
