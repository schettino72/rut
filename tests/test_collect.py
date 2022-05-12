import os
import sys
from pathlib import Path
from contextlib import contextmanager

from rut import check
from rut import fixture, use

from rut.collect import Collector, Selector


SAMPLE_PROJ_ROOT = Path(__file__).parent / 'sample_proj'

@contextmanager
def chdir(new_dir):
    current_dir = os.getcwd()
    try:
        os.chdir(new_dir)
        yield
    finally:
        os.chdir(current_dir)

@fixture
def sample_proj(path=SAMPLE_PROJ_ROOT):
    sys.path.insert(0, path)
    yield
    sys.path.remove(path)


class TestCollector:
    def test_arg_pkg(self):
        sys_path_before = len(sys.path)
        col = Collector()
        pkg_path = str(SAMPLE_PROJ_ROOT / 'proj_inplace')
        col.process_args([pkg_path])
        check(col.mods) == ['proj_inplace.test_bar', 'proj_inplace.test_foo']
        check(sys_path_before) == len(sys.path)  # sys.path is not modified
        check(col.specs) == [('proj_inplace', f'{pkg_path}/__init__.py')]

    def test_arg_module(self):
        col = Collector()
        pkg_path = SAMPLE_PROJ_ROOT / 'proj_inplace'
        mod_path = pkg_path / 'test_bar.py'
        col.process_args([str(mod_path)])
        check(col.mods) == ['proj_inplace.test_bar']
        # specs contains package including module
        check(col.specs) == [('proj_inplace', f'{pkg_path}/__init__.py')]

    def test_arg_invalid(self):
        col = Collector()
        with check.raises(Exception) as exc_info:
            col.process_args(['i_dont_exist'])
        check(exc_info.raised.args[0]) == 'No package: i_dont_exist'

    def test_collect_spec_by_name(self):
        Collector.import_spec('proj_inplace', f'{SAMPLE_PROJ_ROOT}/proj_inplace/__init__.py')
        col = Collector()
        col.collect_by_name('proj_inplace.test_foo')
        check(col.mods) == ['proj_inplace.test_foo']

    def test_guess_dir(self):
        with chdir(SAMPLE_PROJ_ROOT / 'proj_split'):
            col = Collector()
            col.process_args([])
            check(col.mods) == ['tests.test_foo']


class TestSelectCases:
    @use('proj', sample_proj)
    def test_iter(self, proj):
        selector = Selector(['proj_inplace.test_bar', 'proj_inplace.test_foo'])
        selected = [s[:2] for s in  selector.iter_cases()]
        check(selected) == [
            ('proj_inplace.test_bar', 'test_bar'),
            ('proj_inplace.test_foo', 'test_ok'),
            ('proj_inplace.test_foo', 'TestClass.test_xxx'),
            ('proj_inplace.test_foo', 'TestClass.test_abc'),
        ]
