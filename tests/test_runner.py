import types

from rut import check

from rut.collect import Collector
from rut.runner import Runner



def add_test_cases(collector, src, name='this_test'):
    """create module from src text, and add its TestCase's to collector"""
    # FIXME: include source
    # https://stackoverflow.com/questions/62160529/how-to-get-source-inside-exec-python
    module = types.ModuleType(name)
    exec(src, module.__dict__)
    collector.mods.append(name)
    collector.cases[name] = collector._collect_module_tests(module)
    return module


class TestRunnerExecute:
    def test_run_func(self):
        collector = Collector()
        src = """
def test_one():
    assert True
"""
        add_test_cases(collector, src)
        check(collector.cases['this_test']['test_one'].result) == None
        Runner().execute(collector)
        check(collector.cases['this_test']['test_one'].result) == 'SUCCESS'

    def test_run_method(self):
        collector = Collector()
        src = """
class TestMyClass:
    def test_moo(self):
        assert True
"""
        add_test_cases(collector, src)
        check(collector.cases['this_test']['TestMyClass.test_moo'].result) == None
        Runner().execute(collector)
        check(collector.cases['this_test']['TestMyClass.test_moo'].result) == 'SUCCESS'


    def test_run_async(self):
        collector = Collector()
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
        module = add_test_cases(collector, src)
        check(collector.cases['this_test']['test_foo'].result) == None
        check(collector.cases['this_test']['TestMyClass.test_moo'].result) == None
        check(module.track) == []
        Runner().execute(collector)
        check(module.track) == ['foo', 'moo']
        check(collector.cases['this_test']['test_foo'].result) == 'SUCCESS'
        check(collector.cases['this_test']['TestMyClass.test_moo'].result) == 'SUCCESS'



class TestRunnerResult:
    def test_error(self):
        collector = Collector()
        src = """
def inner():
    5/0
def test_one():
    inner()
    assert True
"""
        add_test_cases(collector, src)
        check(collector.cases['this_test']['test_one'].result) == None
        Runner().execute(collector)
        check(collector.cases['this_test']['test_one'].result) == 'ERROR'

    def test_fail(self):
        collector = Collector()
        src = """
from rut import check
def test_one():
    calculated = 6
    check(6) == 3 + 2
"""
        add_test_cases(collector, src)
        check(collector.cases['this_test']['test_one'].result) == None
        Runner().execute(collector)
        check(collector.cases['this_test']['test_one'].result) == 'FAIL'
