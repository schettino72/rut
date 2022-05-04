import io
import sys
import inspect
import logging
import asyncio
from contextlib import redirect_stdout, redirect_stderr

from rich.console import Console
from rich.syntax import Syntax

from .checker import TestFailure
from .collect import Collector


log = logging.getLogger(__name__)

class Runner:
    def __init__(self):
        self.console = Console()

    def execute(self, collector: Collector):
        """execute tests"""
        fixtures = {}
        for mod_name, case_name, case in collector.iter_cases():
            log.info('run %s::%s' % (mod_name, case_name))

            case_out = io.StringIO()
            try:
                # kwargs contain fixtures values for dependency injection
                kwargs = {}
                if case_fixtures := getattr(case.func, 'use_fix', None):
                    for name, fix_func in case_fixtures.items():
                        fixtures[name] = fix_func()
                        kwargs[name] = next(fixtures[name])

                with redirect_stdout(case_out):
                    self._exec_case(case, kwargs)

                # fixture cleanup
                if fixtures:
                    for name in fixtures.keys():
                        next(fixtures[name], None)  # should I check StopIteration was raised?

            except TestFailure as failure:
                case.result = 'FAIL'
                case.io_out = case_out.getvalue()
                self._print_failure(case_name, failure)
                self.console.print(f'++++++++++++++++++\n{case.io_out}\n+++++++++++++++++++++')
            except Exception:
                case.result = 'ERROR'
                case.io_out = case_out
                self.console.print_exception(show_locals=True)
            else:
                case.result = 'SUCCESS'
                self.console.print(f"{mod_name}::{case_name}: [green]OK[/green]")


    def _exec_case(self, case, case_kwargs):
        """execute a single tests case.
        Deal with function/method, async
        """
        is_coro = inspect.iscoroutinefunction(case.func)
        if case.cls:
            obj = case.cls()
            if is_coro:
                asyncio.run(case.func(obj, **case_kwargs))
            else:
                case.func(obj, **case_kwargs)
        else:
            if is_coro:
                asyncio.run(case.func(**case_kwargs))
            else:
                case.func(**case_kwargs)


    def _print_failure(self, case_name, failure: TestFailure):
        console = self.console
        console.print()
        console.rule(f"[bold red]{case_name}", style="red")
        tb = failure.__traceback__
        while tb:
            frame = tb.tb_frame
            tb = tb.tb_next
            if frame.f_globals['__package__'] == 'rut':
                continue
            # rich_inspect(tb, all=True)
            code = frame.f_code
            console.print(f"{code.co_filename}:{frame.f_lineno}: {failure.__class__.__name__}")
            try:
                console.print(Syntax(
                    inspect.getsource(code),
                    'python',
                    start_line=code.co_firstlineno,
                    line_numbers=True,
                    highlight_lines=set([frame.f_lineno]),
                ))
            except OSError:  # can not getsource of code
                pass
        for arg in failure.args[1:]:
            console.print(repr(arg))
        console.rule(style="bright_black", characters="━")
