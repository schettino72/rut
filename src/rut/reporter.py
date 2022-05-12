import importlib
import inspect

from rich.console import Console
from rich.traceback import Traceback
from rich.syntax import Syntax

from .case import FailureInfo


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
