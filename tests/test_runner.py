import unittest
import sys
from rutlib.runner import RutCLI

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
        with self.assertRaises(Exception) as cm:
            cli.load_tests(pattern="sample*.py")

        self.assertIn("is a coroutine but class is not a `unittest.IsolatedAsyncioTestCase`", str(cm.exception))