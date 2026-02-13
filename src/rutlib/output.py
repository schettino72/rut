import logging
import os
import re
import sys
import tempfile
import time
import unittest
from rich.console import Console
from rich.panel import Panel
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
    style = "red"

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
        self._dot_count = 0
        self._term_width = console.width or 80
        self._fd_captures = {}

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
            # FD-level capture: redirect OS file descriptors 1/2 to temp files
            # so subprocess output doesn't leak to terminal
            self._stdout_fd_save = os.dup(1)
            self._stderr_fd_save = os.dup(2)
            self._stdout_fd_tmp = tempfile.TemporaryFile(buffering=0)
            self._stderr_fd_tmp = tempfile.TemporaryFile(buffering=0)
            os.dup2(self._stdout_fd_tmp.fileno(), 1)
            os.dup2(self._stderr_fd_tmp.fileno(), 2)

    def _restoreStdout(self):
        if self.buffer:
            # Restore OS file descriptors before Python-level restore
            os.dup2(self._stdout_fd_save, 1)
            os.dup2(self._stderr_fd_save, 2)
            os.close(self._stdout_fd_save)
            os.close(self._stderr_fd_save)
            self._stdout_fd_tmp.close()
            self._stderr_fd_tmp.close()
            for handler in logging.root.handlers:
                if id(handler) in self._original_handler_streams:
                    handler.stream = self._original_handler_streams[id(handler)]
            self._original_handler_streams.clear()
        super()._restoreStdout()

    def _add_dot(self, char, style):
        self.console.print(Text(char, style=style), end="")
        self.console.file.flush()
        self._dot_count += 1
        max_dots = max(self._term_width - 10, 10)
        if self._dot_count >= max_dots:
            self.console.print()
            self._dot_count = 0

    def _flush_dots(self):
        if self._dot_count > 0:
            self.console.print()
            self._dot_count = 0

    def _save_fd_output(self, test):
        if not self.buffer:
            return
        self._stdout_fd_tmp.seek(0)
        stdout = self._stdout_fd_tmp.read().decode('utf-8', errors='replace')
        self._stderr_fd_tmp.seek(0)
        stderr = self._stderr_fd_tmp.read().decode('utf-8', errors='replace')
        if stdout or stderr:
            self._fd_captures[test.id()] = (stdout, stderr)

    def _print_fd_captures(self, test):
        captures = self._fd_captures.get(test.id())
        if not captures:
            return
        stdout, stderr = captures
        if stdout:
            self.console.print(Panel(
                stdout.rstrip('\n'),
                title="Captured stdout (fd)",
                border_style="dim",
            ))
        if stderr:
            self.console.print(Panel(
                stderr.rstrip('\n'),
                title="Captured stderr (fd)",
                border_style="dim red",
            ))

    def addSuccess(self, test):
        super().addSuccess(test)
        if self.verbose:
            self.console.print(f"[green]✔[/green] {test.id()}")
        else:
            self._add_dot(".", "green")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._save_fd_output(test)
        if self.verbose:
            self.console.print(f"[bold red]✖[/bold red] {test.id()}")
        else:
            self._add_dot("F", "bold red")

    def addError(self, test, err):
        super().addError(test, err)
        self._save_fd_output(test)
        if self.verbose:
            self.console.print(f"[bold red]✖[/bold red] {test.id()}")
        else:
            self._add_dot("E", "bold red")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.verbose:
            self.console.print(f"[yellow]SKIP[/yellow] {test.id()}: {reason}")
        else:
            self._add_dot("s", "yellow")

    def printErrors(self):
        if not self.errors and not self.failures:
            return
        width = self.console.width or 80
        self.console.print()
        for test, err in self.errors:
            self.console.print(_test_header(test.id(), "ERROR", width))
            cleaned = _clean_traceback(err)
            self.console.print(_colorize_diff(cleaned, verbose=self.verbose))
            self._print_fd_captures(test)
        for test, err in self.failures:
            self.console.print(_test_header(test.id(), "FAIL", width))
            cleaned = _clean_traceback(err)
            self.console.print(_colorize_diff(cleaned, verbose=self.verbose))
            self._print_fd_captures(test)


class RichTestRunner:
    def __init__(self, failfast=False, buffer=False, uptodate_modules=None, verbose=False):
        self.failfast = failfast
        self.buffer = buffer
        self.verbose = verbose
        self.uptodate_modules = uptodate_modules or {}
        # Dup stdout fd so console output bypasses fd-level capture (dup2 won't affect this fd)
        console_fd = os.dup(sys.__stdout__.fileno())
        self.console = Console(file=os.fdopen(console_fd, 'w'))

    def run(self, suite):
        result = RichTestResult(self.console, self.buffer, verbose=self.verbose)
        result.failfast = self.failfast
        result.buffer = self.buffer

        # Print up-to-date modules
        if self.uptodate_modules:
            uptodate_total = sum(self.uptodate_modules.values())
            if self.verbose:
                for module, count in self.uptodate_modules.items():
                    self.console.print(f"[yellow]⚡[/yellow] {module} ({count})")
            else:
                n_modules = len(self.uptodate_modules)
                self.console.print(
                    f"[yellow]⚡[/yellow] {n_modules} up-to-date ({uptodate_total} tests)"
                )

        start_time = time.time()
        suite.run(result)
        stop_time = time.time()

        time_taken = stop_time - start_time
        result._flush_dots()
        result.printErrors()

        uptodate_total = sum(self.uptodate_modules.values()) if self.uptodate_modules else 0
        passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
        ok = result.wasSuccessful()
        dash_style = "bold green" if ok else "bold red"

        parts = []
        if result.failures:
            parts.append((f"{len(result.failures)} failed", "red"))
        if result.errors:
            parts.append((f"{len(result.errors)} errors", "bold red"))
        if passed:
            parts.append((f"{passed} passed", "bold green"))
        if uptodate_total:
            parts.append((f"{uptodate_total} up-to-date", "dim yellow"))

        center = Text()
        for i, (text, style) in enumerate(parts):
            if i > 0:
                center.append(", ")
            center.append(text, style=style)
        center.append(f" in {time_taken:.3f}s")

        width = self.console.width or 80
        content_len = len(center.plain) + 2  # spaces around center
        remaining = max(width - content_len, 4)
        left = remaining // 2
        right = remaining - left

        line = Text()
        line.append("─" * left, style=dash_style)
        line.append(f" {center.plain} ")
        line.append("─" * right, style=dash_style)
        # Re-build with styles by using append_text
        line = Text()
        line.append("─" * left, style=dash_style)
        line.append(" ")
        line.append_text(center)
        line.append(" ")
        line.append("─" * right, style=dash_style)
        self.console.print(Text("\n").append_text(line))

        return result
