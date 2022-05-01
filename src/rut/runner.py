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
        for name, test in sorted(collector.tests.items()):
            log.info('run %s' % name)
            try:
                if 'cls' in test:
                    obj = test['cls']()
                    test['func'](obj)
                else:
                    test['func']()
            except TestFailure as failure:
                result = 'FAIL'
                console.print()
                console.rule(f"[bold red]{name}", style="red")
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
                console.print(failure)
                console.rule(style="bright_black", characters="━")
            except Exception:
                result = 'ERROR'
                console.print_exception(show_locals=True)
            else:
                result = 'PASS'
                console.print(f"{name}: [green]OK[/green]")

            test['result'] = result
