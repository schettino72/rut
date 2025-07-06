import unittest
import sys
import warnings
from unittest.mock import patch
from rutlib.runner import RutCLI, InvalidAsyncTestError, WarningCollector

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
    def setUp(self):
        self.original_argv = sys.argv

    def tearDown(self):
        sys.argv = self.original_argv

    def test_discover_all_samples(self):
        sys.argv = ["rut", "tests/samples/discovery"]
        cli = RutCLI()
        suite = cli.load_tests(pattern="sample*.py")
        self.assertEqual(suite.countTestCases(), 4)

    def test_filter_by_keyword(self):
        sys.argv = ["rut", "-k", "feature", "tests/samples/discovery"]
        cli = RutCLI()
        suite = cli.load_tests(pattern="sample*.py")
        self.assertEqual(suite.countTestCases(), 2)

        test_ids = {test.id().split('.')[-1] for test in suite}
        self.assertIn("test_gamma_feature", test_ids)
        self.assertIn("test_delta_feature", test_ids)

    def test_filter_by_filename(self):
        sys.argv = ["rut", "-k", "sample_one", "tests/samples/discovery"]
        cli = RutCLI()
        suite = cli.load_tests(pattern="sample*.py")
        self.assertEqual(suite.countTestCases(), 2)

        test_ids = {test.id().split('.')[-2] for test in suite}
        self.assertIn("SampleOneTests", test_ids)

    def test_load_valid_async_test(self):
        sys.argv = ["rut", "-k", "a_valid_async_test", "tests/samples"]
        cli = RutCLI()
        suite = cli.load_tests(pattern="sample*.py")
        self.assertEqual(suite.countTestCases(), 1)

        test_ids = {test.id().split('.')[-1] for test in suite}
        self.assertIn("test_a_valid_async_test", test_ids)

    def test_fail_on_invalid_async_test(self):
        sys.argv = ["rut", "-k", "invalid_async", "tests/samples"]
        cli = RutCLI()
        with self.assertRaises(InvalidAsyncTestError) as cm:
            cli.load_tests(pattern="sample*.py")

        self.assertIn("is a coroutine but class is not a `unittest.IsolatedAsyncioTestCase`", str(cm.exception))
