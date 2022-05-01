import sys
from pathlib import Path

from rut import check

from rut.collect import Collector


class TestCollectorFindModules:
    def test_init(self):
        col = Collector()
        check(col.mods) == []

    def test_dir(self):
        sample_root = Path(__file__).parent / 'sample_proj'
        sys.path.insert(0, str(sample_root))

        col = Collector()
        col.find_pkg_modules('my_proj')
        check(col.mods) == ['my_proj.test_bar', 'my_proj.test_foo']

    def test_module(self):
        sample_root = Path(__file__).parent / 'sample_proj'
        sys.path.insert(0, str(sample_root))

        col = Collector()
        col.find_pkg_modules('my_proj.test_bar')
        check(col.mods) == ['my_proj.test_bar']


class TestSelectCases:
    def test_iter(self):
        sample_root = Path(__file__).parent / 'sample_proj'
        sys.path.insert(0, str(sample_root))

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
