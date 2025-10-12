import os
import sys
import argparse
import tomllib
import builtins
import time
import unittest
from typing import Dict, List, Any
from rich.console import Console
from rich.panel import Panel


class RutCLI:
    """Command-line interface for the rut test runner.
    
    Handles argument parsing and configuration loading from pyproject.toml.
    """
    
    def __init__(self):
        self.args = self.parse_args()
        self.config = self.load_config()

    def parse_args(self):
        """Parse command-line arguments.
        
        Returns:
            Namespace: Parsed arguments
        """
        from rutlib import __version__
        
        parser = argparse.ArgumentParser(
            description="rut - A modern test runner for Python's unittest framework",
            epilog="For more information, see: https://github.com/schettino72/rut"
        )
        parser.add_argument('--version', action='version', version=f'rut {__version__}')
        parser.add_argument('-k', '--keyword', type=str, help='Only run tests that match the given keyword.')
        parser.add_argument('-x', '--exitfirst', action='store_true', help='Exit on first failure.')
        parser.add_argument('-s', '--capture', action='store_true', help='Disable all output capturing.')
        parser.add_argument('--cov', action='store_true', help='Run with code coverage.')
        parser.add_argument(
            '--test-base-dir', type=str, default=None, help='Base directory for conftest.py discovery.'
        )
        parser.add_argument(
            'test_path', nargs='?', type=str, default=None, help='Path to tests (default: tests).'
        )
        parser.add_argument('--no-color', action='store_true', help='Disable color output.')
        return parser.parse_args()

    @property
    def test_base_dir(self) -> str:
        """Get the base directory for test discovery.
        
        Returns:
            str: The test base directory path
        """
        if self.args.test_base_dir:
            return self.args.test_base_dir
        return self.config.get("test_base_dir", "tests")

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from pyproject.toml.
        
        Returns:
            Dict[str, Any]: Configuration dictionary from [tool.rut] section
        """
        try:
            with open("pyproject.toml", "rb") as f:
                pyproject_data = tomllib.load(f)
                return pyproject_data.get("tool", {}).get("rut", {})
        except FileNotFoundError:
            return {}

    @property
    def coverage_source(self) -> List[str]:
        """Get the coverage source directories.
        
        Returns:
            List[str]: List of source directories for coverage
        """
        # Default coverage source
        cov_source = self.config.get("coverage_source", ["src", "tests"])

        # Check for non-existent source directories
        for source_dir in cov_source:
            if not os.path.isdir(source_dir):
                print(
                    f"Warning: coverage source directory '{source_dir}' does not exist.",
                    file=sys.stderr,
                )
        return cov_source

    def warning_filters(self, filters_spec: List[str]) -> List[Dict[str, Any]]:
        """Parse warning filters from pyproject.toml.
        
        Each filter is a string in the format: "action:message:category:module".
        
        Args:
            filters_spec: List of filter specification strings
            
        Returns:
            List[Dict[str, Any]]: List of filter dictionaries with keys:
                'action', 'message', 'category', 'module'
        """
        filters = []
        for filter_str in filters_spec:
            parts = filter_str.split(":")
            if len(parts) < 3:
                print(f"Warning: Invalid warning filter format '{filter_str}'. Expected 'action:message:category:module'.", file=sys.stderr)
                continue
                
            filter_dict = {
                'action': parts[0],
                'message': parts[1],
                'module': parts[3] if len(parts) > 3 else ""
            }

            category_name = parts[2]
            if category_name:
                try:
                    filter_dict['category'] = getattr(builtins, category_name)
                except AttributeError:
                    print(f"Warning: Could not find warning category '{category_name}'. Skipping filter.", file=sys.stderr)
                    continue
            filters.append(filter_dict)
        return filters


class RichTestResult(unittest.TestResult):
    """Custom test result class with Rich formatting.
    
    Provides colorized output for test results using the Rich library.
    """
    
    def __init__(self, console: Console, buffer: bool, verbosity: int):
        """Initialize the test result.
        
        Args:
            console: Rich Console instance for output
            buffer: Whether to buffer output
            verbosity: Verbosity level
        """
        super().__init__()
        self.console = console

    def addSuccess(self, test: unittest.TestCase) -> None:
        """Record a test success.
        
        Args:
            test: The test case that passed
        """
        super().addSuccess(test)
        self.console.print(f"[green]✔[/green] {test.id()}")

    def addFailure(self, test: unittest.TestCase, err) -> None:
        """Record a test failure.
        
        Args:
            test: The test case that failed
            err: The error information
        """
        super().addFailure(test, err)
        self.console.print(f"[bold red]✖[/bold red] {test.id()}")

    def addError(self, test: unittest.TestCase, err) -> None:
        """Record a test error.
        
        Args:
            test: The test case that had an error
            err: The error information
        """
        super().addError(test, err)
        self.console.print(f"[bold red]✖[/bold red] {test.id()}")

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:
        """Record a test skip.
        
        Args:
            test: The test case that was skipped
            reason: The reason for skipping
        """
        super().addSkip(test, reason)
        self.console.print(f"[yellow]SKIP[/yellow] {test.id()}: {reason}")

    def printErrors(self) -> None:
        """Print all errors and failures that occurred during testing."""
        if self.errors or self.failures:
            self.console.print("\n[bold red]Failures and Errors:[/bold red]")
            if self.errors:
                for test, err in self.errors:
                    self.console.print(Panel(err, title=f"[bold red]ERROR: {test.id()}[/bold red]"))
            if self.failures:
                for test, err in self.failures:
                    self.console.print(Panel(err, title=f"[bold red]FAIL: {test.id()}[/bold red]"))


class RichTestRunner:
    """Test runner with Rich formatting for beautiful output.
    
    Provides a modern, colorized test runner interface.
    """
    
    def __init__(self, failfast: bool = False, buffer: bool = False):
        """Initialize the test runner.
        
        Args:
            failfast: Whether to stop on first failure
            buffer: Whether to buffer test output
        """
        self.failfast = failfast
        self.buffer = buffer
        self.console = Console()

    def run(self, suite: unittest.TestSuite) -> RichTestResult:
        """Run the test suite.
        
        Args:
            suite: The test suite to run
            
        Returns:
            RichTestResult: The test result
        """
        result = RichTestResult(self.console, self.buffer, 0)
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
