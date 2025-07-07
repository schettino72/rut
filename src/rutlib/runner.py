"""
RUT - test runner
"""

import gc
import inspect
import warnings
import unittest
import importlib.util
import asyncio
import os
import time
from rich import print
from rich.panel import Panel
from rich.console import Console

class RutError(Exception):
    """Base exception for the rut runner."""
    pass

class InvalidAsyncTestError(RutError):
    """Raised when a test method is async but the class is not an IsolatedAsyncioTestCase."""
    pass

class WarningCollector:
    """
    Collects all warnings raised during a test run and allows custom filtering.

    This class has two primary functions:
    1.  It installs a hook to capture all warnings, even those that might
        normally be ignored by the default filtering, and prints them at
        the end of the test run.
    2.  It allows the user to provide a list of custom warning filters to
        overwrite the default behavior, for example, to turn specific
        warnings into exceptions.
    """
    # TODO:
    # Print stack traces for warnings
    # warnings.simplefilter("always")
    # warnings.showwarning = lambda message, category, filename, lineno, file=None, line=None: \
    # print(f"{filename}:{lineno}: {category.__name__}: {message}")

    def __init__(self):
        self._original_show = None
        self.collected = []

    def setup(self, extra):
        # unittest by default silent some warnings...
        # FIXME: Should make it explicit.
        # warnings.resetwarnings()
        # warnings.simplefilter("always")

        self._original_show = warnings.showwarning

        def _warn_collector(message, category, filename, lineno, file=None, line=None):
            if category is RuntimeWarning:
                self.collected.append((str(message), category, filename, lineno))
            # always call original function
            self._original_show(message, category, filename, lineno, file, line)

        warnings.showwarning = _warn_collector
        warnings.filterwarnings("always", category=RuntimeWarning)

        # Filter only my_specific_module warnings
        for spec in extra:
            warnings.filterwarnings(
                spec['action'],
                category=spec['category'],
                module=spec['module'])
        gc.collect()


    def cleanup(self):
        if self._original_show:
            warnings.showwarning = self._original_show
            self._original_show = None
            warnings.resetwarnings()

    def print_warnings(self):
        if self.collected:
            print(Panel(
                '\n'.join(
                    f"[yellow]{w[1].__name__}[/yellow]: {w[0]} at [cyan]{w[2]}:{w[3]}[/cyan]"
                    for w in self.collected
                ),
                title="[bold yellow]Collected Warnings[/bold yellow]",
                expand=False,
            ))


class RichTestResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()

    def addSuccess(self, test):
        super().addSuccess(test)
        self.console.print(f"[green]✔[/green] {test.id()}")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.console.print(f"[bold red]✖[/bold red] {test.id()}")

    def addError(self, test, err):
        super().addError(test, err)
        self.console.print(f"[bold red]✖[/bold red] {test.id()}")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.console.print(f"[yellow]SKIP[/yellow] {test.id()}: {reason}")

    def printErrors(self):
        if self.errors or self.failures:
            self.console.print("\n[bold red]Failures and Errors:[/bold red]")
            if self.errors:
                for test, err in self.errors:
                    self.console.print(Panel(err, title=f"[bold red]ERROR: {test.id()}[/bold red]"))
            if self.failures:
                for test, err in self.failures:
                    self.console.print(Panel(err, title=f"[bold red]FAIL: {test.id()}[/bold red]"))


class RichTestRunner:
    def __init__(self, failfast=False, buffer=False):
        self.failfast = failfast
        self.buffer = buffer
        self.console = Console()

    def run(self, suite):
        result = RichTestResult(self.console.file, self.buffer, 0)
        result.failfast = self.failfast
        
        start_time = time.time()
        suite.run(result)
        stop_time = time.time()
        
        time_taken = stop_time - start_time
        result.printErrors()
        
        self.console.print("\n" + ("-" * 70))
        self.console.print(f"Ran {result.testsRun} tests in {time_taken:.3f}s")
        
        if result.wasSuccessful():
            self.console.print("\n[bold green]OK[/bold green]")
        else:
            self.console.print(f"\n[bold red]FAILED[/bold red] (failures={len(result.failures)}, errors={len(result.errors)})")
            
        return result


class RutRunner:
    def __init__(self, test_path, test_base_dir, keyword, failfast, capture, warning_filters):
        self.test_path = test_path
        self.test_base_dir = test_base_dir
        self.keyword = keyword
        self.failfast = failfast
        self.capture = capture
        self.warning_filters = warning_filters
        self.conftest = self._load_conftest()

    def _load_conftest(self):
        conftest_path = os.path.join(self.test_base_dir, "conftest.py")
        if not os.path.exists(conftest_path):
            return None
        spec = importlib.util.spec_from_file_location("conftest", conftest_path)
        conftest = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(conftest)
        return conftest

    def _run_hook(self, hook_name):
        if not self.conftest:
            return
        hook = getattr(self.conftest, hook_name, None)
        if not hook:
            return
        if asyncio.iscoroutinefunction(hook):
            asyncio.run(hook())
        else:
            hook()

    def load_tests(self, pattern="test*.py"):
        """return unittest.suite.TestSuite

        Suite has 3 leves:
        1) suite with all modules
        2) suite per class
        3) actual tests
        """
        loader = unittest.TestLoader()
        suite = loader.discover(self.test_path, pattern=pattern)
        suite = self.sort_tests(suite)
        if self.keyword:
            suite = self._filter_keyword(suite, self.keyword)
        self._check_async(suite)
        return suite

    def run_tests(self, suite):
        self._run_hook("rut_session_setup")
        try:
            runner = RichTestRunner(
                failfast=self.failfast,
                buffer=not self.capture,
            )

            wc = WarningCollector()
            wc.setup(extra=self.warning_filters)
            result = runner.run(suite)
            wc.print_warnings()
            return result
        finally:
            self._run_hook("rut_session_teardown")

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
                        raise InvalidAsyncTestError(
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
