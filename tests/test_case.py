import sys

from rut import check

from rut.checker import CheckFailure
from rut import case


def sample_func(my_param):
    my_var = 6
    check(my_param) == my_var

class TestFailureInfo:
    def test_from_exception(self):
        try:
            sample_func(2)
        except CheckFailure as exc:
            info = case.FailureInfo.from_exception(exc)
            check(info.name) == 'CheckEqualityFailure'
            check(info.args[1]) == 2
            check(info.args[2]) == 6
            check(info.stack[0]['name']) == 'test_from_exception'
            check(info.stack[1]['name']) == 'sample_func'
            check(len(info.stack)) == 2
        else:  # pragma: no cover
            assert False



def sample_error(param):
    my_dict = {'foo': [param]}
    raise ValueError('Not a value')

class TestErrorInfo:
    def test_error_from_exception(self):
        try:
            sample_error(2)
        except ValueError:
            info = case.ErrorInfo.from_exc_info(sys.exc_info())
            check(info.exc_type) == 'ValueError'
            check(info.value.args) == ('Not a value',)
            frames = info.trace.stacks[0].frames
            check(frames[0].name) == 'test_error_from_exception'
            check(frames[1].name) == 'sample_error'
            # Trace(stacks=[Stack(exc_type='ValueError', exc_value='Not a value', syntax_error=None,
            # is_cause=False, frames=[Frame(filename='/home/eduardo/work/rut/tests/test_case.py', lineno=36,
            # name='test_from_exception', line='', locals={'self': Node(key_repr='',
            # value_repr='<tests.test_case.TestFailureInfo object at 0x7f34c5115300>', open_brace='',
            # close_brace='', empty='', last=True, is_tuple=False, is_namedtuple=False, children=None,
            # separator=', ')}), Frame(filename='/home/eduardo/work/rut/tests/test_case.py', lineno=31,
            # name='sample_error', line='', locals={'param': Node(key_repr='', value_repr='2', open_brace='',
            # close_brace='', empty='', last=True, is_tuple=False, is_namedtuple=False, children=None,
            # separator=', ')})])])
            check(frames[1].locals['param'].value_repr) == '2'
        else:  # pragma: no cover
            assert False



class TestCaseOutcome:
    def test_success(self):
        outcome = case.CaseOutcome('test_sample', 'TestOutcome.test_success')
        outcome.result = 'SUCCESS'
        got = outcome.unpack(outcome.pack())
        check(outcome.mod_name) == 'test_sample'
        check(outcome.case_name) == 'TestOutcome.test_success'
        check(outcome.result) == 'SUCCESS'

    def test_failure(self):
        try:
            sample_func(2)
        except CheckFailure as exc:
            outcome = case.CaseOutcome('test_sample', 'TestOutcome.test_failure')
            outcome.result = 'FAIL'
            outcome.failure = case.FailureInfo.from_exception(exc)
            got = outcome.unpack(outcome.pack())
            check(outcome.result) == 'FAIL'
            check(outcome.failure.stack[1]['name']) == 'sample_func'
        else:  # pragma: no cover
            assert False

    def test_error(self):
        try:
            sample_error(2)
        except ValueError as exc:
            outcome = case.CaseOutcome('test_sample', 'TestOutcome.test_error')
            outcome.result = 'ERROR'
            outcome.error = case.ErrorInfo.from_exc_info(sys.exc_info())
            got = outcome.unpack(outcome.pack())
            check(outcome.result) == 'ERROR'
            frame1 = outcome.error.trace.stacks[0].frames[1]
            check(frame1.name) == 'sample_error'
            check(frame1.locals['my_dict'].children[0].children[0].value_repr) == '2'
        else:  # pragma: no cover
            assert False
