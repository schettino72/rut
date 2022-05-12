import io
import sys
import importlib
import inspect
import logging
import asyncio
from contextlib import redirect_stdout
from collections import defaultdict

from rich.console import Console
from rich.traceback import Traceback
from rich.syntax import Syntax

from .checker import CheckFailure
from .case import FailureInfo, ErrorInfo
from .case import TestCase, CaseOutcome
from .collect import Selector


log = logging.getLogger(__name__)



class Runner:
    def __init__(self):
        # mod_name -> test_name: outcome
        self.outcomes: dict[str, dict[str, CaseOutcome]] = defaultdict(dict)


    @staticmethod
    def run_case(mod_name: str, case_name: str, case: TestCase) -> CaseOutcome:
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
            with redirect_stdout(case_out):
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


class Reporter:
    def __init__(self):
        self.console = Console()

    def handle_outcome(self, outcome):
        print = self.console.print
        if outcome.result == 'FAIL':
            assert outcome.failure
            self._print_failure(outcome.case_name, outcome.failure)
            if outcome.io_out:
                print(f"{'*'*20}\n{outcome.io_out}\n{'*'*20}")
        elif outcome.result == 'ERROR':
            # FIXME: suppress by module name does not work
            assert outcome.error
            traceback = Traceback(outcome.error.trace, show_locals=True)
            self.console.print(traceback)
        elif outcome.result == 'SUCCESS':
            print(f"{outcome.mod_name}::{outcome.case_name}: [green]OK[/green]")
        else:  # pragma: no cover
            raise NotImplementedError()


    def _print_failure(self, case_name, failure: FailureInfo):
        """print failure with rich info from checker - ala assert rewrite"""
        console = self.console
        console.print()
        console.rule(f"[bold red]{case_name}", style="red")
        for frame in failure.stack:
            console.print(f"{frame['filename']}:{frame['lineno']}: {failure.name}")

            # find function object referred by the frame
            module = importlib.import_module(frame['module'])
            scope = [module]
            code = None
            while code is None and scope:  # each iteration goes down one level of scope
                down_scope = []
                for this_obj in scope:
                    members = inspect.getmembers(this_obj)
                    for name, obj in members:
                        if inspect.isfunction(obj) and name == frame['name']:
                            if frame['firstlineno'] == obj.__code__.co_firstlineno:
                                code = obj
                                break
                        down_scope.append(obj)
                scope = down_scope
            if not code:
                continue
            # show source of function in frame
            try:
                console.print(Syntax(
                    inspect.getsource(code),
                    'python',
                    start_line=frame['firstlineno'],
                    line_numbers=True,
                    highlight_lines=set([frame['lineno']]),
                ))
            except OSError:  # can not getsource of code
                pass
        for arg in failure.args[1:]:
            console.print(repr(arg))
        console.rule(style="bright_black", characters="━")
