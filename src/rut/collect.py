from __future__ import annotations

from operator import attrgetter
import sys
import logging
import inspect
from pathlib import Path
import importlib
from importlib.util import find_spec, spec_from_file_location, module_from_spec
from importlib.machinery import ModuleSpec
import pkgutil
from types import ModuleType
from typing import Optional

from .case import TestCase


log = logging.getLogger(__name__)


class Collector:
    """
    1) find/load python modules

    2) collect tests from module
    3) select which tests cases will be executed
    """
    def __init__(self):
        # list of module name in dot notation i.e. `<pkg>.<name>`
        self.mods: list[str] = []
        self.specs = []
        self.all_tests = True  # executing all tests

    @staticmethod
    def import_spec(name, fn):
        """import module given file_location spec args"""
        spec = spec_from_file_location(name, fn)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[name] = module
        return spec

    def _import_pkg_path(self, fn):
        """import dir without modifying sys.path"""
        # FIXME: handle sub-package
        pkg_name = Path(fn).name
        spec_args = pkg_name, f'{fn}/__init__.py'
        spec = self.import_spec(*spec_args)
        self.specs.append(spec_args)
        return spec, pkg_name


    def _import_mod_path(self, fn):
        path = Path(fn)
        mod_name = path.stem
        spec_args = (mod_name, fn)  # contain highest pkg or module
        parent = path.parent
        while (parent / '__init__.py').exists():
            mod_name = f'{parent.name}.{mod_name}'
            spec_args = (parent.name, str(parent / '__init__.py'))
            parent = parent.parent
        spec = self.import_spec(*spec_args)
        self.specs.append(spec_args)
        return spec, mod_name

    def process_args(self, args: list[str]):
        """process CLI args, import and keep track of test modules
        """
        # no args specified, search on default paths
        if len(args) == 0:
            # 1) tests
            if Path('tests/__init__.py').exists():
                spec, pkg_name = self._import_pkg_path('tests')
                self.collect_by_name(pkg_name, spec)
            else:
                raise NotImplementedError('check src or local')
        # process CLI / config test spec with paths
        else:
            self.all_tests = False
            for arg in args:
                # 1) is python module?
                if arg.endswith('.py'):
                    spec, mod_name = self._import_mod_path(arg)
                    self.mods.append(mod_name)
                    continue
                # 2) treat file as package dir_path
                if (Path(arg) / '__init__.py').exists():
                    spec, pkg_name = self._import_pkg_path(arg)
                    self.collect_by_name(pkg_name, spec)
                    continue
                # FIXME raise a CLI error
                raise Exception(f'No package: {arg}')


    def collect_by_name(self, name: str, mod_spec: Optional[ModuleSpec] = None):
        """
        """
        if not mod_spec:
            mod_spec = find_spec(name)
        if not mod_spec:
            raise Exception(f'Failed to import "{name}"')
        if mod_spec.parent == mod_spec.name:  # is package
            for info in pkgutil.walk_packages(mod_spec.submodule_search_locations):
                if info.name.startswith('test_'):
                    self.mods.append(f'{mod_spec.name}.{info.name}')
        else:
            self.mods.append(name)


class Selector:
    def __init__(self, mods=None):
        self.mods: list[str] = mods if mods else []
        self.cases: dict[str, TestCase] = {}  # mod_name: {TestCase}
        self.collect_cases()

    @classmethod
    def _collect_module_tests(cls, module: ModuleType):
        """get test functions (test_) from module given by path."""
        tests = {}

        # load functions
        for name, ref in inspect.getmembers(module, inspect.isfunction):
            if name.startswith('test_'):
                tests[ref.__qualname__] = TestCase(ref)

        # load class methods
        for cls_name, cls_ref in inspect.getmembers(module, inspect.isclass):
            if cls_name.startswith('Test'):
                for name, ref in inspect.getmembers(cls_ref, inspect.isfunction):
                    if name.startswith('test_'):
                        tests[ref.__qualname__] = TestCase(ref, cls=cls_ref)
        return tests


    def collect_cases(self):
        for mod_name in self.mods:
            log.info('load: %s' % mod_name)
            module = importlib.import_module(mod_name)
            self.cases[mod_name] = self._collect_module_tests(module)


    def iter_cases(self):
        for mod_name, cases in sorted(self.cases.items()):
            for case in sorted(cases.values(), key=attrgetter('lineno')):
                yield mod_name, case.func.__qualname__, case
