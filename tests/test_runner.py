import sys
import io
import types
from contextlib import redirect_stdout

from rut import check

from rut.collect import Selector
from rut.runner import Runner, Reporter


import tempfile
from importlib import util
import importlib.machinery


def add_test_cases(selector, src, name='this_test'):
    """create module from src text, and add its TestCase's to collector"""

    with tempfile.NamedTemporaryFile(suffix='.py') as tmp:
        tmp.write(src.encode())
        tmp.flush()

        spec = util.spec_from_file_location('tmp', tmp.name)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules['tmp'] = module

        selector.mods.append(name)
        selector.cases[name] = selector._collect_module_tests(module)
        return module

def run_all(selector, report=False):
    runner = Runner()
    reporter = Reporter()
    for outcome in runner.execute(selector):
        if report:
            reporter.handle_outcome(outcome)
    return runner

class TestRunnerExecute:
    def test_run_func(self):
        selector = Selector()
        src = """
def test_one():
    assert True
"""
        add_test_cases(selector, src)
        runner = run_all(selector)
        check(runner.outcomes['this_test']['test_one'].result) == 'SUCCESS'

    def test_run_method(self):
        selector = Selector()
        src = """
class TestMyClass:
    def test_moo(self):
        assert True
"""
        add_test_cases(selector, src)
        runner = run_all(selector)
        check(runner.outcomes['this_test']['TestMyClass.test_moo'].result) == 'SUCCESS'


    def test_run_async(self):
        selector = Selector()
        src = """
track = []
async def some_val(val):
    return val

async def test_foo():
    track.append(await some_val('foo'))
    assert True

class TestMyClass:
    async def test_moo(self):
        track.append(await some_val('moo'))
        assert True
"""
        module = add_test_cases(selector, src)
        check(module.track) == []
        runner = run_all(selector)
        check(module.track) == ['foo', 'moo']
        check(runner.outcomes['this_test']['test_foo'].result) == 'SUCCESS'
        check(runner.outcomes['this_test']['TestMyClass.test_moo'].result) == 'SUCCESS'



class TestRunnerResult:
    def test_error(self):
        selector = Selector()
        src = """
def inner():
    5/0
def test_one():
    inner()
    assert True
"""
        add_test_cases(selector, src)
        runner = run_all(selector)
        check(runner.outcomes['this_test']['test_one'].result) == 'ERROR'

    def test_fail(self):
        selector = Selector()
        src = """
from rut import check
def test_one():
    calculated = 6
    check(6) == 3 + 2
"""
        add_test_cases(selector, src)
        runner = run_all(selector)
        check(runner.outcomes['this_test']['test_one'].result) == 'FAIL'



class TestIO:
    def test_capture_sucess(self):
        selector = Selector()
        src ="""
def test_print():
    print('IGNORE>>')
"""
        add_test_cases(selector, src)
        runner_out = io.StringIO()
        with redirect_stdout(runner_out):
            run_all(selector, True)
        check(runner_out.getvalue()) == 'this_test::test_print: OK\n'


    def test_output_error(self):
        selector = Selector()
        src ="""
from rut import check
def test_print():
    print('CLUE-HERE')
    check(1) == 2
"""
        add_test_cases(selector, src)
        runner_out = io.StringIO()
        with redirect_stdout(runner_out):
            run_all(selector, True)
        got = runner_out.getvalue()
        assert 'CLUE-HERE' in got

