import logging
import sys
import time
import unittest
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def _clean_traceback(tb_string):
    """Strip internal unittest/rutlib frames from a traceback string.

    Keeps only user code frames. If all frames are internal, returns the
    original traceback unchanged.
    """
    lines = tb_string.splitlines(keepends=True)
    cleaned = []
    skip_next = False
    internal_patterns = ('/unittest/', '/rutlib/')
    for line in lines:
        if skip_next:
            skip_next = False
            continue
        if line.strip().startswith('File "'):
            if any(p in line for p in internal_patterns):
                skip_next = True
                continue
        cleaned.append(line)
    # If we stripped everything except the header and exception line, fall back
    user_frames = [ln for ln in cleaned if ln.strip().startswith('File "')]
    if not user_frames and any(ln.strip().startswith('File "') for ln in lines):
        return tb_string
    return ''.join(cleaned)


def _colorize_diff(tb_string):
    """Return a rich.text.Text with colorized diff lines.

    When a '? ' pointer line follows a '-' or '+' line, the pointer
    characters (^, +, -, ~) mark which chars differ.  Instead of showing
    the '?' line, we highlight those chars with a background on the
    preceding line.
    """
    result = Text()
    lines = tb_string.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        stripped = lines[i].rstrip('\n')
        if not stripped:
            i += 1
            continue
        # Peek ahead for a ? pointer line
        pointer = None
        if i + 1 < len(lines) and lines[i + 1].rstrip('\n').startswith('? '):
            pointer = lines[i + 1].rstrip('\n')

        if stripped.startswith('- '):
            if pointer:
                _append_highlighted(result, stripped, pointer, "white on #3b1219", "bold white on #72232d")
                i += 2
            else:
                result.append(stripped + '\n', style="white on #3b1219")
                i += 1
        elif stripped.startswith('+ '):
            if pointer:
                _append_highlighted(result, stripped, pointer, "white on #122b17", "bold white on #1f6b2b")
                i += 2
            else:
                result.append(stripped + '\n', style="white on #122b17")
                i += 1
        elif stripped.startswith('? '):
            # Orphan ? line (no preceding +/- consumed it), skip
            i += 1
        elif stripped.startswith('File '):
            result.append(stripped + '\n', style="cyan")
            i += 1
        elif stripped.startswith('Traceback '):
            result.append(stripped + '\n', style="dim")
            i += 1
        else:
            result.append(lines[i])
            i += 1
    return result


def _append_highlighted(result, content_line, pointer_line, base_style, highlight_style):
    """Append a diff line, highlighting chars marked by the ? pointer."""
    pointer = pointer_line[2:]  # strip '? ' prefix
    prefix = content_line[:2]   # '- ' or '+ '
    body = content_line[2:]

    result.append(prefix, style=base_style)
    for j, ch in enumerate(body):
        if j < len(pointer) and pointer[j] in ('^', '+', '-', '~'):
            result.append(ch, style=highlight_style)
        else:
            result.append(ch, style=base_style)
    result.append('\n', style=base_style)


class RichTestResult(unittest.TestResult):
    def __init__(self, console, buffer: bool, verbosity):
        super().__init__()
        self.console = console
        self._original_handler_streams = {}

    def _setupStdout(self):
        super()._setupStdout()
        if self.buffer:
            for handler in logging.root.handlers:
                if hasattr(handler, 'stream'):
                    if handler.stream is self._original_stdout:
                        self._original_handler_streams[id(handler)] = handler.stream
                        handler.stream = self._stdout_buffer
                    elif handler.stream is self._original_stderr:
                        self._original_handler_streams[id(handler)] = handler.stream
                        handler.stream = self._stderr_buffer

    def _restoreStdout(self):
        if self.buffer:
            for handler in logging.root.handlers:
                if id(handler) in self._original_handler_streams:
                    handler.stream = self._original_handler_streams[id(handler)]
            self._original_handler_streams.clear()
        super()._restoreStdout()

    def addSuccess(self, test):
        super().addSuccess(test)
        self.console.print(f"[green]✔[/green] {test.id()}")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.console.print(f"[bold red]✖[/bold red] {test.id()}")

    def addError(self, test, err):
        super().addError(test, err)
        self.console.print(f"[bold red]✖[/bold red] {test.id()}")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.console.print(f"[yellow]SKIP[/yellow] {test.id()}: {reason}")

    def printErrors(self):
        if self.errors or self.failures:
            self.console.print("\n[bold red]Failures and Errors:[/bold red]")
            if self.errors:
                for test, err in self.errors:
                    cleaned = _clean_traceback(err)
                    colorized = _colorize_diff(cleaned)
                    self.console.print(Panel(colorized, title=f"[bold red]ERROR: {test.id()}[/bold red]"))
            if self.failures:
                for test, err in self.failures:
                    cleaned = _clean_traceback(err)
                    colorized = _colorize_diff(cleaned)
                    self.console.print(Panel(colorized, title=f"[bold red]FAIL: {test.id()}[/bold red]"))


class RichTestRunner:
    def __init__(self, failfast=False, buffer=False, skipped_modules=None):
        self.failfast = failfast
        self.buffer = buffer
        self.skipped_modules = skipped_modules or {}
        # Use sys.__stdout__ to bypass capture - test progress should always be visible
        self.console = Console(file=sys.__stdout__)

    def run(self, suite):
        result = RichTestResult(self.console, self.buffer, 0)
        result.failfast = self.failfast
        result.buffer = self.buffer

        # Print skipped (up-to-date) modules first
        for module, count in self.skipped_modules.items():
            self.console.print(f"[yellow]⚡[/yellow] {module} ({count})")

        start_time = time.time()
        suite.run(result)
        stop_time = time.time()

        time_taken = stop_time - start_time
        result.printErrors()

        self.console.print("\n" + ("-" * 70))
        self.console.print(f"Ran {result.testsRun} tests in {time_taken:.3f}s")

        if result.wasSuccessful():
            self.console.print("\n[bold green]OK[/bold green]")
        else:
            self.console.print(f"\n[bold red]FAILED[/bold red] (failures={len(result.failures)}, errors={len(result.errors)})")

        return result
