import os
import sys
import argparse
import tomllib
import builtins
import time
import unittest
from rich.console import Console
from rich.panel import Panel


class RutCLI:
    def __init__(self):
        self.args = self.parse_args()
        self.config = self.load_config()

    def parse_args(self):
        parser = argparse.ArgumentParser(description="RUT")
        parser.add_argument('-k', '--keyword', type=str, help='Only run tests that match.')
        parser.add_argument('-x', '--exitfirst', action='store_true', help='Exit on first failure.')
        parser.add_argument('-s', '--capture', action='store_true', help='Disable all capturing')
        parser.add_argument('--cov', action='store_true', help='Code Coverage')
        parser.add_argument(
            '--test-base-dir', type=str, default=None, help='Base directory for tests.'
        )
        parser.add_argument(
            'test_path', nargs='?', type=str, default=None, help='Path to tests.'
        )
        parser.add_argument('--no-color', action='store_true', help='Disable color output.')
        return parser.parse_args()

    @property
    def test_base_dir(self):
        if self.args.test_base_dir:
            return self.args.test_base_dir
        return self.config.get("test_base_dir", "tests")

    def load_config(self):
        try:
            with open("pyproject.toml", "rb") as f:
                pyproject_data = tomllib.load(f)
                return pyproject_data.get("tool", {}).get("rut", {})
        except FileNotFoundError:
            return {}

    @property
    def coverage_source(self):
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

    def warning_filters(self, filters_spec):
        """
        Parses warning filters from pyproject.toml.

        Each filter is a string in the format: "action:message:category:module".
        Returns a list of dictionaries, each with the keys:
        'action', 'message', 'category', 'module'.
        """
        filters = []
        for filter_str in filters_spec:
            parts = filter_str.split(":")
            assert len(parts) >= 3
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
                    print(f"Warning: Could not find warning category '{category_name}'. Defaulting to 'Warning'.", file=sys.stderr)
            filters.append(filter_dict)
        return filters


class RichTestResult(unittest.TestResult):
    def __init__(self, console, buffer: bool, verbosity):
        super().__init__()
        self.console = console

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
