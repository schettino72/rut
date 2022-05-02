import inspect
import logging

from rich.console import Console
from rich.syntax import Syntax
from rich import inspect as rich_inspect

from .checker import TestFailure
from .collect import Collector


log = logging.getLogger(__name__)
console = Console()

class Runner:
    def __init__(self):
        pass

    def execute(self, collector: Collector):
        """execute tests"""
        fixtures = {}
        for mod_name, case_name, case in collector.iter_cases():
            log.info('run %s::%s' % (mod_name, case_name))
            try:
                kwargs = {}
                if case_fixtures := getattr(case.func, 'use_fix', None):
                    for name, fix_func in case_fixtures.items():
                        fixtures[name] = fix_func()
                        kwargs[name] = next(fixtures[name])
                if case.cls:
                    obj = case.cls()
                    case.func(obj, **kwargs)
                else:
                    case.func(**kwargs)
                if fixtures:
                    for name in fixtures.keys():
                        next(fixtures[name], None)  # should I check StopIteration was raised?

            except TestFailure as failure:
                result = 'FAIL'
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
                    console.print(Syntax(
                        inspect.getsource(code),
                        'python',
                        start_line=code.co_firstlineno,
                        line_numbers=True,
                        highlight_lines=set([frame.f_lineno]),
                    ))
                for arg in failure.args:
                    console.print(arg)
                console.rule(style="bright_black", characters="━")
            except Exception:
                result = 'ERROR'
                console.print_exception(show_locals=True)
            else:
                result = 'PASS'
                console.print(f"{mod_name}::{case_name}: [green]OK[/green]")

            case.result = result
