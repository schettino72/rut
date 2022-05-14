import io
import sys
import inspect
import logging
import asyncio
from contextlib import nullcontext, redirect_stdout
from collections import defaultdict

from .checker import CheckFailure
from .case import FailureInfo, ErrorInfo
from .case import TestCase, CaseOutcome
from .collect import Selector


log = logging.getLogger(__name__)



class Runner:
    def __init__(self, capture='sys'):
        # mod_name -> test_name: outcome
        self.outcomes: dict[str, dict[str, CaseOutcome]] = defaultdict(dict)
        self.capture: str = capture  # supports: sys, no

    def run_case(self, mod_name: str, case_name: str, case: TestCase) -> CaseOutcome:
        """run a single TestCase, returns a CaseOutcome"""
        fixtures = {}
        case_out = io.StringIO()
        outcome = CaseOutcome(mod_name, case_name)
        try:
            # kwargs contain fixtures values for dependency injection
            kwargs = {}
            if case_fixtures := getattr(case.func, 'use_fix', None):
                for name, fix in case_fixtures.items():
                    fixtures[name] = fix.func(*fix.args, **fix.kwargs)
                    kwargs[name] = next(fixtures[name])

            # TODO: stderr, logs
            with redirect_stdout(case_out) if self.capture == 'sys' else nullcontext():
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

            # fixture cleanup
            if fixtures:
                for name in fixtures.keys():
                    next(fixtures[name], None)  # should I check StopIteration was raised?

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
        for mod_name, case_name, case in selector.iter_cases():
            log.info('run %s::%s' % (mod_name, case_name))
            outcome = self.run_case(mod_name, case_name, case)
            self.outcomes[mod_name][case_name] = outcome
            yield outcome
