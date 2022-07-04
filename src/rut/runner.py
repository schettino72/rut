import io
import sys
import inspect
import logging
import asyncio
import itertools
from contextlib import contextmanager, nullcontext, redirect_stdout, redirect_stderr
from collections import defaultdict

from .checker import CheckFailure
from .case import FailureInfo, ErrorInfo, SkippedTest
from .case import TestCase, CaseOutcome
from .collect import Selector


log = logging.getLogger(__name__)


@contextmanager
def capsys(case_out, case_err):
    with redirect_stdout(case_out), redirect_stderr(case_err):
        yield


# https://stackoverflow.com/a/40623158/64444
def parametrization_product(params):
    """
    >>> list(parametrization_product(dict(number=[1,2], character='ab')))
    [{'character': 'a', 'number': 1},
     {'character': 'a', 'number': 2},
     {'character': 'b', 'number': 1},
     {'character': 'b', 'number': 2}]
    """
    if not params:
        # if no parametrization return an empty dict, so a single case is executed
        return ({},)
    else:
        return (dict(zip(params, x)) for x in itertools.product(*params.values()))


class Runner:
    """manages running a tests and producing TestOutcome.

    It has no knowledge of mutli-processing. On MP, One instance per test module.
    """
    def __init__(self, capture='sys'):
        # mod_name -> test_name: outcome
        # FIXME: should not save outcomes
        self.outcomes: dict[str, dict[str, CaseOutcome]] = defaultdict(dict)
        self.capture: str = capture  # supports: sys, no

    def run_case(self,
                 mod_name: str,
                 case_name: str,
                 case: TestCase,
                 kwargs: dict) -> CaseOutcome:
        """run a single TestCase, returns a CaseOutcome"""
        case_out = io.StringIO()
        case_err = io.StringIO()
        outcome = CaseOutcome(mod_name, case_name)
        try:
            # TODO: logs
            with capsys(case_out, case_err) if self.capture == 'sys' else nullcontext():
                is_coro = inspect.iscoroutinefunction(case.func)
                if case.cls:
                    obj = case.cls()
                    if is_coro:
                        asyncio.run(case.func(obj, **kwargs))
                    else:
                        case.func(obj, **kwargs)
                else:
                    if is_coro:
                        asyncio.run(case.func(**kwargs))
                    else:
                        case.func(**kwargs)

        except CheckFailure as failure:
            outcome.result = 'FAIL'
            outcome.io_out = case_out.getvalue()
            outcome.failure = FailureInfo.from_exception(failure)
        except SkippedTest as skipped:
            outcome.result = 'SKIPPED'
            outcome.io_out = case_out.getvalue()
            outcome.skip = skipped.reason
        except Exception:
            outcome.result = 'ERROR'
            outcome.io_out = case_out.getvalue()
            outcome.error = ErrorInfo.from_exc_info(sys.exc_info())  # type: ignore
        else:
            outcome.result = 'SUCCESS'
        return outcome


    def execute(self, selector: Selector):
        """execute tests"""
        for mod_name, base_name, case in selector.iter_cases():
            log.info('run %s::%s' % (mod_name, base_name))

            # manage fixtures
            # kwargs contain fixtures values for dependency injection
            fix_single = {}
            fix_parametrized = {}

            # split fixtures into single or parametrized
            if case_fixtures := getattr(case.func, 'use_fix', None):
                for name, fix in reversed(case_fixtures.items()):
                    # TODO: friendly error message if @use is passed a non-fixture
                    assert fix.func.rut_scope == 'function'

                    if not fix.params:
                        fix_single[name] = fix
                    else:
                        fix_parametrized[name] = fix.params

            for parametrization_spec in parametrization_product(fix_parametrized):
                case_name = base_name
                fix_in_use = {}  # name: fixture generator
                kwargs = {}  # kwargs for case (with fixture values)

                # non-parametrized
                for name, fix in fix_single.items():
                    fix_kwargs = fix.kwargs.copy()
                    fix_in_use[name] = fix.func(*fix.args, **fix_kwargs)
                    kwargs[name] = next(fix_in_use[name])


                for name in fix_parametrized.keys():
                    fix = case_fixtures[name]
                    fix_kwargs = fix.kwargs.copy()
                    param = parametrization_spec[name]
                    fix_kwargs['param'] = param
                    param_name = getattr(param, '__name__', str(param))
                    case_name += f'[{param_name}]'

                    fix_in_use[name] = fix.func(*fix.args, **fix_kwargs)
                    kwargs[name] = next(fix_in_use[name])

                outcome = self.run_case(mod_name, case_name, case, kwargs)

                # fixture cleanup
                if fix_in_use:
                    for name in fix_in_use.keys():
                        # should I check StopIteration was raised?
                        next(fix_in_use[name], None)

                self.outcomes[mod_name][case_name] = outcome
                yield outcome
