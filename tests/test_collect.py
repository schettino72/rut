import sys
from pathlib import Path
from contextlib import contextmanager

from rut import check
from rut import fixture, use

from rut.collect import Collector


SAMPLE_PROJ_ROOT = str(Path(__file__).parent / 'sample_proj')

@contextmanager
def add_sys_path(path: str):
    sys.path.insert(0, path)
    yield
    sys.path.remove(path)

@fixture
def sample_proj():
    path = str(Path(__file__).parent / 'sample_proj')
    sys.path.insert(0, path)
    yield
    sys.path.remove(path)


class TestCollectorFindModules:
    def test_init(self):
        col = Collector()
        check(col.mods) == []

    def test_dir(self):
        with add_sys_path(SAMPLE_PROJ_ROOT):
            col = Collector()
            col.find_pkg_modules('my_proj')
            check(col.mods) == ['my_proj.test_bar', 'my_proj.test_foo']

    @use('proj', sample_proj)
    def test_module(self, proj):
        col = Collector()
        col.find_pkg_modules('my_proj.test_bar')
        check(col.mods) == ['my_proj.test_bar']


class TestSelectCases:
    @use('proj', sample_proj)
    def test_iter(self, proj):
        col = Collector()
        col.find_pkg_modules('my_proj')
        col.collect_cases()
        selected = [s[:2] for s in  col.iter_cases()]
        check(selected) == [
            ('my_proj.test_bar', 'test_bar'),
            ('my_proj.test_foo', 'test_ok'),
            ('my_proj.test_foo', 'TestClass.test_xxx'),
            ('my_proj.test_foo', 'TestClass.test_abc'),
        ]
