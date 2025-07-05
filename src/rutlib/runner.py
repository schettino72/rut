"""
RUT - test runner
"""

import argparse
import gc
import inspect
import warnings
import unittest

class WarningCollector:
    # TODO:
    # Print stack traces for warnings
    # warnings.simplefilter("always")
    # warnings.showwarning = lambda message, category, filename, lineno, file=None, line=None: \
    # print(f"{filename}:{lineno}: {category.__name__}: {message}")

    def __init__(self):
        self._original_show = None
        self.collected = []

    def setup(self):
        # unittest by default silent some warnings...
        # FIXME: Should make it explicit.
        # warnings.resetwarnings()

        self._original_show = warnings.showwarning

        def _warn_collector(message, category, filename, lineno, file=None, line=None):
            if category is RuntimeWarning:
                self.collected.append((str(message), category, filename, lineno))
            # always call original function
            self._original_show(message, category, filename, lineno, file, line)

        warnings.showwarning = _warn_collector
        warnings.filterwarnings("always", category=RuntimeWarning)

        # FIXME: make this configurable -
        # Filter only Pydantic warnings
        warnings.filterwarnings("error", category=UserWarning, module="pydantic")
        gc.collect()

    def print_warnings(self):
        if self.collected:
            print('==== RUT collected warnings:')
        for warn in self.collected:
            warnings_str = f"{warn[1].__name__} => {warn[0]} at {warn[2]}:{warn[3]}"
            print("---- Warning \n", warnings_str)
            print("----")


class RutCLI:
    """
    Usage:
      runner = RutCLI()
      suite = runner.load_tests()
      runner.run_tests(suite)
    """

    def __init__(self):
        self.args = self.parse_args()

    def parse_args(self):
        parser = argparse.ArgumentParser(description="RUT")
        parser.add_argument('-k', '--keyword', type=str, help='Only run tests that match.')
        parser.add_argument('-x', '--exitfirst', action='store_true', help='Exit on first failure.')
        parser.add_argument('-s', '--capture', action='store_true', help='Disable all capturing')
        # FIXME
        # parser.add_argument('--pdb', action='store_true', help='Drop in pdb on error')
        parser.add_argument('--cov', action='store_true', help='Code Coverage')
        parser.add_argument(
            'test_path', nargs='?', type=str, default='tests', help='Path to tests.'
        )
        return parser.parse_args()

    @classmethod
    def _filter_keyword(cls, suite, keyword, level=1):
        """return new suite containing only tests with given keyword
        Note that original Suite tree strucutre is modified / flaten

        If keywork is in lowercase ignore case
        """
        filtered = unittest.TestSuite()
        keyword_islower = keyword.islower()
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                # print('-'* level + '>')
                filtered.addTests(cls._filter_keyword(test, keyword, level=level + 1))
            else:
                # print('-'* level, test.id())
                # test.id contains module, class and function names
                # i.e. test_testing.TestCalcSessionSummary.test_finish_session
                test_id = test.id().lower() if keyword_islower else test.id()
                if keyword in test_id:
                    filtered.addTest(test)
        return filtered

    @classmethod
    def _check_async(cls, suite):
        """sanity check (async) for test definitions
        IF test method is a co-routine, class must be a IsolatedAsyncioTestCase
        """
        for test in suite:
            if isinstance(test, unittest.TestSuite):  # recurse
                cls._check_async(test)
            else:
                test_method = getattr(test, test._testMethodName)
                if inspect.iscoroutinefunction(test_method):
                    if not isinstance(test, unittest.IsolatedAsyncioTestCase):
                        # TODO: clean error output to user
                        raise Exception(
                            f'Testing method is a coroutine but class is not a `unittest.IsolatedAsyncioTestCase` => {test.id()}'
                        )

    @staticmethod
    def test_pos_key(test):
        """return tuple to used as key to sort unit tests"""
        method_code = getattr(test, test._testMethodName).__code__
        method_lineno = getattr(method_code, "co_firstlineno", 0)
        return (test.__module__, method_lineno)

    @classmethod
    def flatten(cls, suite):
        flat = unittest.TestSuite()
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                flat.addTests(cls.flatten(test))
            else:
                flat.addTest(test)
        return flat

    @classmethod
    def sort_tests(cls, suite):
        """sort test by module / position(line) in module

        Default is to execute in alphabetical order :/
        """
        flat_suite = cls.flatten(suite)
        pos_suite = unittest.TestSuite()
        for test in sorted(flat_suite, key=cls.test_pos_key):
            pos_suite.addTest(test)
        return pos_suite

    def load_tests(self, pattern="test*.py"):
        """return unittest.suite.TestSuite

        Suite has 3 leves:
        1) suite with all modules
        2) suite per class
        3) actual tests
        """
        loader = unittest.TestLoader()
        suite = loader.discover(self.args.test_path, pattern=pattern)
        suite = self.sort_tests(suite)
        if self.args.keyword:
            suite = self._filter_keyword(suite, self.args.keyword)
        self._check_async(suite)
        return suite

    def run_tests(self, suite):
        runner = unittest.TextTestRunner(
            verbosity=2,
            buffer=not self.args.capture,
            failfast=self.args.exitfirst,
        )

        wc = WarningCollector()
        wc.setup()
        result = runner.run(suite)  # unittest.TextTestResult
        wc.print_warnings()
        return result