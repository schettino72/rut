"""
RUT - test runner

A modern test runner for Python's unittest framework with async support.
"""

import gc
import inspect
import warnings
import unittest
import importlib.util
import asyncio
import os
from typing import List, Dict, Any, Tuple, Optional, Callable
from rich import print
from rich.panel import Panel


class RutError(Exception):
    """Base exception for the rut runner."""
    pass


class InvalidAsyncTestError(RutError):
    """Raised when a test method is async but the class is not an IsolatedAsyncioTestCase."""
    pass


class WarningCollector:
    """Collects all warnings raised during a test run and allows custom filtering.

    This class has two primary functions:
    1. It installs a hook to capture all warnings, even those that might
       normally be ignored by the default filtering, and prints them at
       the end of the test run.
    2. It allows the user to provide a list of custom warning filters to
       overwrite the default behavior, for example, to turn specific
       warnings into exceptions.
    """

    def __init__(self):
        """Initialize the warning collector."""
        self._original_show: Optional[Callable] = None
        self.collected: List[Tuple[str, type, str, int]] = []

    def setup(self, extra: List[Dict[str, Any]]) -> None:
        """Set up warning collection with optional custom filters.
        
        Args:
            extra: List of custom warning filter specifications
        """
        self._original_show = warnings.showwarning

        def _warn_collector(message, category, filename, lineno, file=None, line=None):
            if category is RuntimeWarning:
                self.collected.append((str(message), category, filename, lineno))
            # always call original function
            if self._original_show:
                self._original_show(message, category, filename, lineno, file, line)

        warnings.showwarning = _warn_collector
        warnings.filterwarnings("always", category=RuntimeWarning)

        # Apply custom warning filters
        for spec in extra:
            warnings.filterwarnings(
                spec['action'],
                category=spec['category'],
                module=spec['module'])
        gc.collect()


    def cleanup(self) -> None:
        """Clean up and restore original warning settings."""
        if self._original_show:
            warnings.showwarning = self._original_show
            self._original_show = None
            warnings.resetwarnings()

    def print_warnings(self) -> None:
        """Print all collected warnings in a formatted panel."""
        if self.collected:
            print(Panel(
                '\n'.join(
                    f"[yellow]{w[1].__name__}[/yellow]: {w[0]} at [cyan]{w[2]}:{w[3]}[/cyan]"
                    for w in self.collected
                ),
                title="[bold yellow]Collected Warnings[/bold yellow]",
                expand=False,
            ))


class RutRunner:
    """Core test runner for rut.
    
    Handles test discovery, filtering, validation, and execution.
    """
    
    def __init__(
        self,
        test_path: str,
        test_base_dir: str,
        keyword: Optional[str],
        failfast: bool,
        capture: bool,
        warning_filters: List[Dict[str, Any]]
    ):
        """Initialize the test runner.
        
        Args:
            test_path: Path to discover tests from
            test_base_dir: Base directory for conftest.py discovery
            keyword: Optional keyword filter for test selection
            failfast: Whether to stop on first failure
            capture: Whether to capture test output
            warning_filters: List of custom warning filter specifications
        """
        self.test_path = test_path
        self.test_base_dir = test_base_dir
        self.keyword = keyword
        self.failfast = failfast
        self.capture = capture
        self.warning_filters = warning_filters
        self.conftest = self._load_conftest()

    def _load_conftest(self) -> Optional[Any]:
        """Load conftest.py if it exists in the test base directory.
        
        Returns:
            The loaded conftest module or None if not found
        """
        conftest_path = os.path.join(self.test_base_dir, "conftest.py")
        if not os.path.exists(conftest_path):
            return None
        spec = importlib.util.spec_from_file_location("conftest", conftest_path)
        if spec is None or spec.loader is None:
            return None
        conftest = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(conftest)
        return conftest

    def _run_hook(self, hook_name: str) -> None:
        """Run a hook function from conftest.py if it exists.
        
        Supports both synchronous and asynchronous hook functions.
        
        Args:
            hook_name: Name of the hook function to run
        """
        if not self.conftest:
            return
        hook = getattr(self.conftest, hook_name, None)
        if not hook:
            return
        if asyncio.iscoroutinefunction(hook):
            asyncio.run(hook())
        else:
            hook()

    def load_tests(self, pattern: str = "test*.py") -> unittest.TestSuite:
        """Load and discover tests from the test path.
        
        Returns a test suite with tests sorted by their definition order
        and filtered by keyword if specified.

        Args:
            pattern: File pattern for test discovery (default: "test*.py")
            
        Returns:
            A unittest.TestSuite containing all discovered tests
        """
        loader = unittest.TestLoader()
        suite = loader.discover(self.test_path, pattern=pattern)
        suite = self.sort_tests(suite)
        if self.keyword:
            suite = self._filter_keyword(suite, self.keyword)
        self._check_async(suite)
        return suite

    def run_tests(
        self,
        suite: unittest.TestSuite,
        runner_class: Optional[type] = None
    ) -> unittest.TestResult:
        """Run the test suite with session hooks.
        
        Executes rut_session_setup before tests and rut_session_teardown after,
        even if tests fail.
        
        Args:
            suite: The test suite to run
            runner_class: Optional custom test runner class
            
        Returns:
            The test result
        """
        self._run_hook("rut_session_setup")
        try:
            if runner_class:
                runner = runner_class(
                    failfast=self.failfast,
                    buffer=not self.capture,
                )
            else:
                runner = unittest.TextTestRunner(
                    verbosity=2,
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
    def _filter_keyword(
        cls,
        suite: unittest.TestSuite,
        keyword: str,
        level: int = 1
    ) -> unittest.TestSuite:
        """Filter tests by keyword match in test ID.
        
        Returns a new suite containing only tests with the given keyword.
        Note that the original suite tree structure is flattened.
        
        Args:
            suite: The test suite to filter
            keyword: Keyword to match against test IDs
            level: Current recursion level (internal use)
            
        Returns:
            A new TestSuite with only matching tests
        """
        filtered = unittest.TestSuite()
        keyword_islower = keyword.islower()
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                filtered.addTests(cls._filter_keyword(test, keyword, level=level + 1))
            else:
                # test.id contains module, class and function names
                # i.e. test_testing.TestCalcSessionSummary.test_finish_session
                test_id = test.id().lower() if keyword_islower else test.id()
                if keyword in test_id:
                    filtered.addTest(test)
        return filtered

    @classmethod
    def _check_async(cls, suite: unittest.TestSuite) -> None:
        """Validate async test definitions.
        
        Ensures that coroutine test methods are in IsolatedAsyncioTestCase classes.
        
        Args:
            suite: The test suite to validate
            
        Raises:
            InvalidAsyncTestError: If an async test is not in an IsolatedAsyncioTestCase
        """
        for test in suite:
            if isinstance(test, unittest.TestSuite):  # recurse
                cls._check_async(test)
            else:
                test_method = getattr(test, test._testMethodName)
                if inspect.iscoroutinefunction(test_method):
                    if not isinstance(test, unittest.IsolatedAsyncioTestCase):
                        raise InvalidAsyncTestError(
                            f'Test method "{test.id()}" is a coroutine but its class is not '
                            f'a unittest.IsolatedAsyncioTestCase. To fix this, change the '
                            f'test class to inherit from unittest.IsolatedAsyncioTestCase.'
                        )

    @staticmethod
    def test_pos_key(test: unittest.TestCase) -> Tuple[str, int]:
        """Get sort key for a test based on its module and line number.
        
        Args:
            test: The test case
            
        Returns:
            Tuple of (module_name, line_number) for sorting
        """
        method_code = getattr(test, test._testMethodName).__code__
        method_lineno = getattr(method_code, "co_firstlineno", 0)
        return (test.__module__, method_lineno)

    @classmethod
    def flatten(cls, suite: unittest.TestSuite) -> unittest.TestSuite:
        """Flatten a nested test suite into a single-level suite.
        
        Args:
            suite: The test suite to flatten
            
        Returns:
            A flattened TestSuite
        """
        flat = unittest.TestSuite()
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                flat.addTests(cls.flatten(test))
            else:
                flat.addTest(test)
        return flat

    @classmethod
    def sort_tests(cls, suite: unittest.TestSuite) -> unittest.TestSuite:
        """Sort tests by their definition order (module, then line number).
        
        By default, unittest runs tests in alphabetical order.
        This method sorts them by the order they appear in source files.
        
        Args:
            suite: The test suite to sort
            
        Returns:
            A new TestSuite with tests sorted by definition order
        """
        flat_suite = cls.flatten(suite)
        pos_suite = unittest.TestSuite()
        for test in sorted(flat_suite, key=cls.test_pos_key):
            pos_suite.addTest(test)
        return pos_suite
