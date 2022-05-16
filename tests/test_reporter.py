import io
from contextlib import redirect_stdout

from rut.collect import Selector
from rut.runner import Runner
from rut.reporter import Reporter
from rut import check
from .util import add_test_cases


def run_all(selector):
    runner = Runner()
    reporter = Reporter()
    for outcome in runner.execute(selector):
        reporter.handle_outcome(outcome)
    return runner



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
            run_all(selector)
        check(runner_out.getvalue()) == 'this_test::test_print: OK\n'


    def test_capture_stderr(self):
        selector = Selector()
        src ="""
import sys
def test_print():
    sys.stderr.write('IGNORE STDERR')
"""
        add_test_cases(selector, src)
        runner_out = io.StringIO()
        with redirect_stdout(runner_out):
            run_all(selector)
        check(runner_out.getvalue()) == 'this_test::test_print: OK\n'


    def test_failure_output_stderr(self):
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
            run_all(selector)
        got = runner_out.getvalue()
        check(got).contains('CLUE-HERE')


    def test_error(self):
        selector = Selector()
        src ="""
def test_no():
    5/0
"""
        add_test_cases(selector, src)
        runner_out = io.StringIO()
        with redirect_stdout(runner_out):
            run_all(selector)
        check(runner_out.getvalue()).has_line('ZeroDivisionError: division by zero')
