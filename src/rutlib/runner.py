"""
RUT - test runner
"""

import asyncio
import gc
import importlib.util
import inspect
import os
import pathlib
import unittest
import warnings

from import_deps import ModuleSet, topological_sort, get_all_imports
from rich import print
from rich.panel import Panel

from .cache import get_modified_files


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


class RutRunner:
    def __init__(self, test_path, test_base_dir, keyword, failfast, capture, warning_filters, alpha=False, source_dirs=None, verbose=False, changed=False):
        self.test_path = test_path
        self.test_base_dir = test_base_dir
        self.keyword = keyword
        self.failfast = failfast
        self.capture = capture
        self.warning_filters = warning_filters
        self.alpha = alpha
        self.source_dirs = source_dirs or ["src", "tests"]
        self.verbose = verbose
        self.changed = changed
        self.module_filepaths = {}
        self.module_all_imports = {}
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
        # TODO:         """report on failures importing modules due to syntax error"""
        # import fnmatch
        # for root, _, files in os.walk(self.test_path):
        #     for f in files:
        #         if f.endswith(".py") and fnmatch.fnmatch(f, pattern):
        #             module_path = os.path.join(root, f)
        #             spec = importlib.util.spec_from_file_location(f[:-3], module_path)
        #             module = importlib.util.module_from_spec(spec)
        #             spec.loader.exec_module(module)

        loader = unittest.TestLoader()
        suite = loader.discover(self.test_path, pattern=pattern)
        suite = self.sort_tests(suite)
        if self.keyword:
            suite = self._filter_keyword(suite, self.keyword)
        if self.changed:
            modified_files = get_modified_files(self.source_dirs)
            suite, self.skipped_modules = self._filter_modified(suite, modified_files)
        else:
            self.skipped_modules = {}
        self._check_async(suite)
        return suite

    def run_tests(self, suite, runner_class=None):
        self._run_hook("rut_session_setup")
        try:
            if runner_class:
                runner = runner_class(
                    failfast=self.failfast,
                    buffer=not self.capture,
                    skipped_modules=self.skipped_modules,
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

    def _filter_modified(self, suite, modified_files, skipped=None):
        """Filter suite to only include tests from modified files or their dependencies.

        Returns (filtered_suite, skipped_modules) where skipped_modules is
        a dict of module_name -> test_count for unchanged modules.
        """
        if skipped is None:
            skipped = {}

        # Build set of modified module names from filepaths
        modified_modules = set()
        filepath_to_module = {fp: mod for mod, fp in self.module_filepaths.items()}
        for fp in modified_files:
            if fp in filepath_to_module:
                modified_modules.add(filepath_to_module[fp])

        if self.verbose:
            print("[DEBUG --changed] Modified files:", modified_files)
            print("[DEBUG --changed] Modified modules:", modified_modules)

        # Build mapping: short module name -> full module name
        short_to_full = {}
        seen_modules = set()
        for mod_name in self.module_all_imports:
            short_name = mod_name.rsplit('.', 1)[-1]
            if short_name not in short_to_full:
                short_to_full[short_name] = mod_name

        filtered = unittest.TestSuite()
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                sub_filtered, _ = self._filter_modified(test, modified_files, skipped)
                filtered.addTests(sub_filtered)
            else:
                # Get the full module name for this test
                test_module = test.__module__
                full_module = short_to_full.get(test_module, test_module)

                # Get all transitive imports for this test module
                all_imports = self.module_all_imports.get(full_module, set())

                # Test is affected if:
                # 1. Test file itself is modified, OR
                # 2. Any transitive import is modified
                test_affected = (
                    full_module in modified_modules or
                    bool(all_imports & modified_modules)
                )

                if self.verbose and full_module not in seen_modules:
                    print(f"[DEBUG] {full_module}: deps={all_imports}, affected={test_affected}")
                    seen_modules.add(full_module)

                if test_affected:
                    filtered.addTest(test)
                else:
                    skipped[test.__module__] = skipped.get(test.__module__, 0) + 1
        return filtered, skipped

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

    def sort_tests(self, suite):
        """Sort tests by topological order of import dependencies.

        Tests for modules with fewer dependencies run first.
        Within each module, tests run in source line order.

        If self.alpha is True, use alphabetical ordering instead.
        """
        flat_suite = self.flatten(suite)

        # Group tests by module
        tests_by_module = {}
        for test in flat_suite:
            mod = test.__module__
            tests_by_module.setdefault(mod, []).append(test)

        # Sort tests within each module by line number
        for tests in tests_by_module.values():
            tests.sort(key=self.test_pos_key)

        if self.alpha:
            # Alphabetical ordering (legacy)
            sorted_modules = sorted(tests_by_module.keys())
        else:
            # Topological ordering by import dependencies
            sorted_modules = self._get_topological_order(tests_by_module.keys())

        # Build final suite
        pos_suite = unittest.TestSuite()
        for mod_name in sorted_modules:
            if mod_name in tests_by_module:
                for test in tests_by_module[mod_name]:
                    pos_suite.addTest(test)

        return pos_suite

    def _get_topological_order(self, test_modules):
        """Get topological order of test modules based on import dependencies."""
        # Find all .py files from configured source directories
        py_files = []
        for source_dir in self.source_dirs:
            source_path = pathlib.Path(source_dir)
            if source_path.is_dir():
                for path in source_path.rglob('*.py'):
                    py_files.append(str(path))

        if not py_files:
            return sorted(test_modules)

        # Build module set and get imports
        try:
            module_set = ModuleSet(py_files)
            results = []
            for mod_fqn, mod in module_set.by_name.items():
                imports = module_set.mod_imports(mod_fqn)
                results.append({
                    'module': mod_fqn,
                    'filepath': str(mod.path),
                    'imports': sorted(imports),
                })

            sort_result = topological_sort(results)

            if self.verbose:
                print("Import dependency ranking:")
                for mod in sort_result.modules:
                    print(f"  {mod}: level={sort_result.levels[mod]}, depth={sort_result.depths[mod]}")
                print()

            # Store filepaths mapping for use in _filter_modified
            self.module_filepaths = sort_result.filepaths

            # Store transitive imports for each module
            self.module_all_imports = get_all_imports(results)

            # Build mapping: short name -> full name for matching test modules
            # unittest may load as 'test_zebra' or 'tests.samples.topo.test_zebra'
            sorted_test_modules = []
            seen = set()

            for full_name in sort_result.modules:
                short_name = full_name.rsplit('.', 1)[-1]
                for test_mod in test_modules:
                    if test_mod not in seen:
                        if test_mod == full_name or test_mod == short_name:
                            sorted_test_modules.append(test_mod)
                            seen.add(test_mod)

            # Add any test modules not found in the graph (isolated)
            for mod in sorted(test_modules):
                if mod not in seen:
                    sorted_test_modules.append(mod)

            return sorted_test_modules
        except Exception:
            # Fallback to alphabetical if import analysis fails
            return sorted(test_modules)
