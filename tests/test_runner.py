from rut import check


from rut.collect import Selector
from rut.runner import Runner
from .util import add_test_cases



def run_all(selector):
    runner = Runner()
    tuple(runner.execute(selector))
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


    def test_fixture(self):
        src = """
from rut import check, use

def my_fixture(arg):
    yield arg

@use('five', my_fixture, 5)
def test_fix(five):
    check(five) == 5
"""
        selector = Selector()
        add_test_cases(selector, src)
        runner = run_all(selector)
        check(runner.outcomes['this_test']['test_fix'].result) == 'SUCCESS'



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
