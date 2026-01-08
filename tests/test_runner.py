import logging
import os
import sys
import unittest
import warnings
from unittest.mock import patch
from rutlib.runner import RutRunner, InvalidAsyncTestError, WarningCollector
from rutlib.cli import RichTestRunner

class TestWarningCollector(unittest.TestCase):
    def setUp(self):
        self.wc = WarningCollector()

    def tearDown(self):
        self.wc.cleanup()

    def test_collects_runtime_warnings(self):
        self.wc.setup([])
        with patch.object(self.wc, 'collected', []):
            warnings.warn("This is a test warning", RuntimeWarning)
            self.assertEqual(len(self.wc.collected), 1)
            self.assertIn("This is a test warning", self.wc.collected[0][0])

    def test_by_default_warning_no_raise(self):
        with warnings.catch_warnings():
            self.wc.setup([])
            from tests.samples import my_specific_module
            my_specific_module.do_warning()

    def test_warning_raise(self):
        with warnings.catch_warnings():
            self.wc.setup([{'action': 'error', 'category': UserWarning, 'module':'' }])
            with self.assertRaises(UserWarning):
                from tests.samples import my_specific_module
                my_specific_module.do_warning()

    def test_warning_raise_module_only_not_raised(self):
        with warnings.catch_warnings():
            self.wc.setup([{
                'action': 'error',
                'category': UserWarning,
                'module':'lalala',
            }])
            # not raised because dont match lalala
            from tests.samples import my_specific_module
            my_specific_module.do_warning()

    def test_warning_raise_module_only(self):
        with warnings.catch_warnings():
            self.wc.setup([{
                'action': 'error',
                'category': UserWarning,
                'module':'tests.samples.my_specific_module',
            }])
            with self.assertRaises(UserWarning):
                from tests.samples import my_specific_module
                my_specific_module.do_warning()


class TestRunner(unittest.TestCase):
    def test_discover_all_samples(self):
        runner = RutRunner('tests/samples/discovery', 'tests', None, False, False, [])
        suite = runner.load_tests(pattern="sample*.py")
        self.assertEqual(suite.countTestCases(), 4)

    def test_filter_by_keyword(self):
        runner = RutRunner('tests/samples/discovery', 'tests', 'feature', False, False, [])
        suite = runner.load_tests(pattern="sample*.py")
        self.assertEqual(suite.countTestCases(), 2)

        test_ids = {test.id().split('.')[-1] for test in suite}
        self.assertIn("test_gamma_feature", test_ids)
        self.assertIn("test_delta_feature", test_ids)

    def test_filter_by_filename(self):
        runner = RutRunner('tests/samples/discovery', 'tests', 'sample_one', False, False, [])
        suite = runner.load_tests(pattern="sample*.py")
        self.assertEqual(suite.countTestCases(), 2)

        test_ids = {test.id().split('.')[-2] for test in suite}
        self.assertIn("SampleOneTests", test_ids)

    def test_load_valid_async_test(self):
        runner = RutRunner('tests/samples', 'tests', 'a_valid_async_test', False, False, [])
        suite = runner.load_tests(pattern="sample*.py")
        self.assertEqual(suite.countTestCases(), 1)

        test_ids = {test.id().split('.')[-1] for test in suite}
        self.assertIn("test_a_valid_async_test", test_ids)

    def test_fail_on_invalid_async_test(self):
        runner = RutRunner('tests/samples', 'tests', 'invalid_async', False, False, [])
        with self.assertRaises(InvalidAsyncTestError) as cm:
            runner.load_tests(pattern="sample*.py")

        self.assertIn("is a coroutine but class is not a `unittest.IsolatedAsyncioTestCase`", str(cm.exception))

    def test_filter_by_keyword_nested(self):
        runner = RutRunner('tests', 'tests', 'nested_feature', False, False, [])
        
        # Create a nested suite manually
        suite = unittest.TestSuite()
        nested_suite = unittest.TestSuite()
        
        class TestNested(unittest.TestCase):
            def test_nested_feature(self):
                pass
            def test_another(self):
                pass

        nested_suite.addTest(TestNested('test_nested_feature'))
        nested_suite.addTest(TestNested('test_another'))
        suite.addTest(nested_suite)

        filtered_suite = runner._filter_keyword(suite, "nested_feature")
        self.assertEqual(filtered_suite.countTestCases(), 1)
        test_ids = {test.id().split('.')[-1] for test in filtered_suite}
        self.assertIn("test_nested_feature", test_ids)


class TestRunnerHooks(unittest.TestCase):
    def setUp(self):
        # Ensure the temp file doesn't exist before a test run
        if os.path.exists("tests/samples/setup.tmp"):
            os.remove("tests/samples/setup.tmp")
        if os.path.exists("tests/samples/teardown.tmp"):
            os.remove("tests/samples/teardown.tmp")

    def tearDown(self):
        # Clean up just in case a test fails and teardown isn't called
        if os.path.exists("tests/samples/setup.tmp"):
            os.remove("tests/samples/setup.tmp")
        if os.path.exists("tests/samples/teardown.tmp"):
            os.remove("tests/samples/teardown.tmp")

    def test_hooks_are_called(self):
        """
        Tests that rut_session_setup and rut_session_teardown are called.
        """
        runner = RutRunner(
            test_path='tests/samples',
            test_base_dir='tests/samples',
            keyword='HookCheckTest', # Only run our hook check test
            failfast=False,
            capture=False,
            warning_filters=[]
        )

        # The file should not exist before the test run
        self.assertFalse(os.path.exists("tests/samples/setup.tmp"))
        self.assertFalse(os.path.exists("tests/samples/teardown.tmp"))

        # Load and run the tests
        suite = runner.load_tests(pattern="test_hook_check.py")
        result = runner.run_tests(suite, runner_class=RichTestRunner)

        self.assertTrue(os.path.exists("tests/samples/setup.tmp"))
        self.assertTrue(os.path.exists("tests/samples/teardown.tmp"))

        # Ensure the test itself passed
        self.assertTrue(result.wasSuccessful())


class TestLoggingCapture(unittest.TestCase):
    def setUp(self):
        self.original_handlers = logging.root.handlers[:]
        self.original_level = logging.root.level

    def tearDown(self):
        logging.root.handlers = self.original_handlers
        logging.root.level = self.original_level

    def test_logging_output_captured_with_rich_runner(self):
        """Test that logging output is captured when buffer=True with RichTestRunner."""
        import io
        from io import StringIO

        logging.basicConfig(level=logging.INFO, force=True)

        captured_stderr = StringIO()
        original_stderr = sys.stderr

        class LoggingTest(unittest.TestCase):
            def test_with_logging(self):
                logging.info("This log message should be captured")

        try:
            sys.stderr = captured_stderr
            runner = RichTestRunner(buffer=True)
            result = runner.run(LoggingTest('test_with_logging'))
        finally:
            sys.stderr = original_stderr

        leaked_output = captured_stderr.getvalue()
        self.assertNotIn("This log message should be captured", leaked_output,
                         "Logging output leaked to stderr instead of being captured")
