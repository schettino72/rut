import io
import sys
import inspect
import logging
import asyncio
from contextlib import contextmanager, nullcontext, redirect_stdout, redirect_stderr
from collections import defaultdict

from .checker import CheckFailure
from .case import FailureInfo, ErrorInfo
from .case import TestCase, CaseOutcome
from .collect import Selector


log = logging.getLogger(__name__)


@contextmanager
def capsys(case_out, case_err):
    with redirect_stdout(case_out), redirect_stderr(case_err):
        yield

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
            kwargs = {}
            if case_fixtures := getattr(case.func, 'use_fix', None):
                fix_in_use = {}
                for name, fix in case_fixtures.items():
                    # TODO: friendly error message if @use is passed a non-fixture
                    assert fix.func.rut_scope == 'function'
                    # None indicates no parametrization
                    for param in (fix.params or [None]):
                        fix_kwargs = fix.kwargs.copy()
                        if param is not None:
                            fix_kwargs['param'] = param
                            case_name = f'{base_name}[{param}]'
                        else:
                            case_name = base_name
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

            else:  # no fixtures - FIXME: DRY
                outcome = self.run_case(mod_name, base_name, case, kwargs)
                self.outcomes[mod_name][base_name] = outcome
                yield outcome
