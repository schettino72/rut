from __future__ import annotations

from operator import attrgetter
import logging
import inspect
from pathlib import Path
import importlib
import importlib.util
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
        self.cases: dict[str, TestCase] = {}  # mod_name: {test_name, TestCase}

    def find_pkg_modules(self, name: str):
        mod_spec: Optional[ModuleSpec] = importlib.util.find_spec(name)
        if not mod_spec:
            raise Exception(f'Failed to import "{name}"')
        if mod_spec.parent == mod_spec.name:  # is package
            for info in pkgutil.walk_packages(mod_spec.submodule_search_locations):
                if info.name.startswith('test_'):
                    self.mods.append(f'{name}.{info.name}')
        else:
            self.mods.append(name)

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


    # TODO: create a selector class
    def iter_cases(self):
        for mod_name, cases in sorted(self.cases.items()):
            for case in sorted(cases.values(), key=attrgetter('lineno')):
                yield mod_name, case.func.__qualname__, case




def collect_paths(specs):
    """return Collector
    """
    collector = Collector()

    # no args specified, search on default paths
    if len(specs) == 0:
        # 1) tests
        test_dir = Path('tests')
        if test_dir.exists():
            collector.find_pkg_modules(str(test_dir))
        else:
            raise NotImplementedError('check src or local')
    # process CLI / config test spec with paths
    else:
        for spec in specs:
            collector.find_pkg_modules(spec)

    # collected all tests from found modules
    collector.collect_cases()
    return collector
