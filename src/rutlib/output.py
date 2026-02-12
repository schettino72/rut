import logging
import re
import sys
import time
import unittest
from rich.console import Console
from rich.text import Text

_file_re = re.compile(r'^(\s*File ")(.+)(",\s*line\s*)(\d+)(?:(,\s*in\s*)(.+))?$')
_exc_re = re.compile(r'^(\w+(?:Error|Exception))\b(.*)')


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


def _append_file_line(result, match):
    """Append a parsed File line with per-component styles."""
    prefix, path, mid, lineno, in_part, func = match.groups()
    # Split path into directory + filename
    sep = path.rfind('/')
    if sep >= 0:
        directory = path[:sep + 1]
        filename = path[sep + 1:]
    else:
        directory = ''
        filename = path
    result.append(prefix, style="dim")
    if directory:
        result.append(directory, style="dim")
    result.append(filename, style="bold cyan")
    result.append(mid, style="dim")
    result.append(lineno, style="yellow")
    if in_part and func:
        result.append(in_part, style="dim")
        result.append(func, style="cyan")
    result.append('\n')


def _colorize_diff(tb_string, verbose=False):
    """Return a rich.text.Text with colorized diff lines.

    When a '? ' pointer line follows a '-' or '+' line, the pointer
    characters (^, +, -, ~) mark which chars differ.  Instead of showing
    the '?' line, we highlight those chars with a background on the
    preceding line.

    When verbose is False, the Traceback header is dropped and prose lines
    between the exception and the diff are suppressed.
    """
    result = Text()
    lines = tb_string.splitlines(keepends=True)
    after_exception = False
    has_diff = False
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
        elif stripped.startswith('Traceback '):
            if verbose:
                result.append(stripped + '\n', style="dim")
            i += 1
        else:
            file_m = _file_re.match(stripped)
            exc_m = _exc_re.match(stripped)
            if file_m:
                _append_file_line(result, file_m)
            elif exc_m and not after_exception:
                result.append(exc_m.group(1), style="bold yellow")
                result.append(exc_m.group(2) + '\n')
                after_exception = True
                has_diff = any(
                    lines[j].rstrip('\n').startswith(('- ', '+ '))
                    for j in range(i + 1, len(lines))
                )
            elif stripped.startswith((' ', '\t')) and not after_exception:
                # Indented code line in traceback (unstyled, distinct from dim File parts)
                result.append(stripped + '\n')
            elif stripped.startswith((' ', '\t')) and after_exception:
                # Diff context line (after exception)
                result.append(stripped + '\n', style="dim")
            elif after_exception and has_diff and not verbose:
                # Prose between exception and diff — suppress
                pass
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


def _test_header(test_id, label, width):
    """Build a rule-style header line.

    ── test_module ──────── TestClass.test_method ──────── FAIL ──
    """
    dash = "─"
    style = "red" if label == "FAIL" else "yellow"

    # Split test_id into module name and Class.method
    parts = test_id.split('.')
    module = ""
    class_method = test_id
    for i, part in enumerate(parts):
        if part and part[0].isupper():
            module = parts[i - 1] if i > 0 else ""
            class_method = '.'.join(parts[i:])
            break

    left = f" {module} " if module else " "
    center = f" {class_method} "
    right = f" {label} "

    content_len = 2 + len(left) + len(center) + len(right) + 2
    remaining = max(width - content_len, 6)
    d1 = remaining // 4
    d2 = remaining - d1 - 2  # push FAIL toward right end
    d3 = 2

    result = Text()
    result.append(dash * 2, style=f"dim {style}")
    result.append(left, style=f"dim {style}")
    result.append(dash * d1, style=f"dim {style}")
    result.append(center, style=f"bold {style}")
    result.append(dash * d2, style=f"dim {style}")
    result.append(right, style=f"bold {style}")
    result.append(dash * d3, style=f"dim {style}")
    return result


class RichTestResult(unittest.TestResult):
    def __init__(self, console, buffer: bool, verbose=False):
        super().__init__()
        self.console = console
        self.verbose = verbose
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
        if not self.errors and not self.failures:
            return
        width = self.console.width or 80
        self.console.print()
        for test, err in self.errors:
            self.console.print(_test_header(test.id(), "ERROR", width))
            cleaned = _clean_traceback(err)
            self.console.print(_colorize_diff(cleaned, verbose=self.verbose))
        for test, err in self.failures:
            self.console.print(_test_header(test.id(), "FAIL", width))
            cleaned = _clean_traceback(err)
            self.console.print(_colorize_diff(cleaned, verbose=self.verbose))


class RichTestRunner:
    def __init__(self, failfast=False, buffer=False, skipped_modules=None, verbose=False):
        self.failfast = failfast
        self.buffer = buffer
        self.verbose = verbose
        self.skipped_modules = skipped_modules or {}
        # Use sys.__stdout__ to bypass capture - test progress should always be visible
        self.console = Console(file=sys.__stdout__)

    def run(self, suite):
        result = RichTestResult(self.console, self.buffer, verbose=self.verbose)
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
