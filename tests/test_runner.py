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


class TestFixtures:
    def test_fixture(self):
        src = """
from rut import check, fixture, use

@fixture
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

    def test_fixture_implicit_name(self):
        src = """
from rut import check, fixture, use

@fixture
def five(arg):
    yield arg

@use(five, 5)
def test_fix(five):
    check(five) == 5
"""
        selector = Selector()
        add_test_cases(selector, src)
        runner = run_all(selector)
        check(runner.outcomes['this_test']['test_fix'].result) == 'SUCCESS'


    def test_parametrized(self):
        src = """
from rut import check, fixture, use

@fixture(params=[1, 2])
def my_fixture(param):
    yield param

@use('number', my_fixture)
def test_param_fix(number):
    check(number) == number
"""
        selector = Selector()
        add_test_cases(selector, src)
        runner = run_all(selector)
        check(len(runner.outcomes['this_test'])) == 2
        check(runner.outcomes['this_test']['test_param_fix[1]'].result) == 'SUCCESS'
        check(runner.outcomes['this_test']['test_param_fix[2]'].result) == 'SUCCESS'


    def test_parametrized_multi(self):
        src = """
from rut import check, fixture, use

@fixture(params=[1, 2])
def fix1(param):
    yield param

@fixture(params=[4, 5])
def fix2(param):
    yield param

@use('number1', fix1)
@use('number2', fix2)
def test_param_fix(number1, number2):
    pass
"""
        selector = Selector()
        add_test_cases(selector, src)
        runner = run_all(selector)
        check(len(runner.outcomes['this_test'])) == 4
        check(runner.outcomes['this_test']).contains('test_param_fix[1][4]')
        check(runner.outcomes['this_test']['test_param_fix[1][4]'].result) == 'SUCCESS'
        check(runner.outcomes['this_test']['test_param_fix[1][5]'].result) == 'SUCCESS'
        check(runner.outcomes['this_test']['test_param_fix[2][4]'].result) == 'SUCCESS'
        check(runner.outcomes['this_test']['test_param_fix[2][5]'].result) == 'SUCCESS'



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


    def test_skip(self):
        selector = Selector()
        src = """
from rut import skip_test
def test_skip():
    skip_test('the reason')
"""
        add_test_cases(selector, src)
        runner = run_all(selector)
        check(runner.outcomes['this_test']['test_skip'].result) == 'SKIPPED'
