import argparse
import builtins
import importlib.metadata
import logging
import os
import pathlib
import sys
import time
import tomllib
import unittest
from rich.console import Console
from rich.panel import Panel


class RutCLI:
    def parse_args(self, argv=None):
        parser = argparse.ArgumentParser(description="RUT")
        parser.add_argument('-V', '--version', action='version',
                            version=f"rut {importlib.metadata.version('rut')}")
        parser.add_argument('-k', '--keyword', type=str, help='Only run tests that match.')
        parser.add_argument('-x', '--exitfirst', action='store_true', help='Exit on first failure.')
        parser.add_argument('-s', '--capture', action='store_true', help='Disable all capturing')
        parser.add_argument('--cov', action='store_true', help='Code Coverage')
        parser.add_argument(
            '--test-base-dir', type=str, default=None,
            help='Base directory for tests (default: "tests", configurable in pyproject.toml).'
        )
        parser.add_argument(
            'test_path', nargs='?', type=str, default=None,
            help='Path to test directory or file. Overrides --test-base-dir and config.'
        )
        parser.add_argument('--no-color', action='store_true', help='Disable color output.')
        parser.add_argument('-a', '--alpha', action='store_true',
                            help='Sort tests alphabetically instead of by import dependencies')
        parser.add_argument('--dry-run', action='store_true',
                            help='List tests in execution order without running them')
        parser.add_argument('-v', '--verbose', action='store_true',
                            help='Show verbose output including import dependency ranking')
        parser.add_argument('-c', '--changed', action='store_true',
                            help='Run tests only from files changed since last successful run')
        self.args = parser.parse_args(argv)

    def setup(self):
        self.config = self.load_config()
        self.test_dir = self._resolve_test_dir()
        self.source_dirs = self._resolve_source_dirs()

    def load_config(self):
        stderr = Console(stderr=True)
        cwd = pathlib.Path.cwd()
        # Look in cwd, then parent if cwd is "tests/"
        candidates = [cwd]
        if cwd.name == "tests":
            candidates.append(cwd.parent)
        for directory in candidates:
            pyproject = directory / "pyproject.toml"
            if pyproject.is_file():
                self.project_root = directory
                if directory != cwd:
                    os.chdir(directory)
                with open(pyproject, "rb") as f:
                    pyproject_data = tomllib.load(f)
                    config = pyproject_data.get("tool", {}).get("rut", {})
                    if not config:
                        stderr.print("[yellow]Warning: no \\[tool.rut] section in pyproject.toml. Defaults: test_dir=tests  source_dirs=src, tests[/yellow]")
                    return config
        self.project_root = cwd
        stderr.print("[yellow]Warning: no pyproject.toml found. Defaults: test_dir=.  source_dirs=.[/yellow]")
        return {}

    def _resolve_test_dir(self):
        if self.args.test_base_dir:
            base = self.args.test_base_dir
        else:
            default = "tests" if self.config else "."
            base = str(self.project_root / self.config.get("test_base_dir", default))
        if not os.path.isdir(base):
            print(f"Error: test directory '{base}' does not exist.", file=sys.stderr)
            sys.exit(1)
        return base

    def _resolve_source_dirs(self):
        if "source_dirs" in self.config:
            dirs = [str(self.project_root / d) for d in self.config["source_dirs"]]
        elif self.config:
            dirs = [str(self.project_root / d) for d in ["src", "tests"]]
        else:
            dirs = ["."]

        invalid = [d for d in dirs if not os.path.isdir(d)]
        if invalid and (self.args.cov or self.args.changed):
            print(f"Error: source directories do not exist: {', '.join(invalid)}",
                  file=sys.stderr)
            sys.exit(1)
        return dirs

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
        self._original_handler_streams = {}

    def _setupStdout(self):
        super()._setupStdout()
        if self.buffer:
            for handler in logging.root.handlers:
                if hasattr(handler, 'stream'):
                    if handler.stream is self._original_stdout:
                        self._original_handler_streams[id(handler)] = handler.stream
                        handler.stream = self._stdout_buffer
                    elif handler.stream is self._original_stderr:
                        self._original_handler_streams[id(handler)] = handler.stream
                        handler.stream = self._stderr_buffer

    def _restoreStdout(self):
        if self.buffer:
            for handler in logging.root.handlers:
                if id(handler) in self._original_handler_streams:
                    handler.stream = self._original_handler_streams[id(handler)]
            self._original_handler_streams.clear()
        super()._restoreStdout()

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
    def __init__(self, failfast=False, buffer=False, skipped_modules=None):
        self.failfast = failfast
        self.buffer = buffer
        self.skipped_modules = skipped_modules or {}
        # Use sys.__stdout__ to bypass capture - test progress should always be visible
        self.console = Console(file=sys.__stdout__)

    def run(self, suite):
        result = RichTestResult(self.console, self.buffer, 0)
        result.failfast = self.failfast
        result.buffer = self.buffer

        # Print skipped (up-to-date) modules first
        for module, count in self.skipped_modules.items():
            self.console.print(f"[yellow]⚡[/yellow] {module} ({count})")

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
