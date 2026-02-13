import subprocess
import sys
import unittest
from io import StringIO
from rich.console import Console
from rich.text import Text
from rutlib.output import _clean_traceback, _colorize_diff, _test_header
from rutlib.output import RichTestResult, RichTestRunner


class TestCleanTraceback(unittest.TestCase):
    def test_strips_unittest_frames(self):
        tb = (
            'Traceback (most recent call last):\n'
            '  File "/usr/lib/python3.12/unittest/case.py", line 123, in run\n'
            '    testMethod()\n'
            '  File "tests/test_math.py", line 12, in test_add\n'
            '    self.assertEqual(4, 5)\n'
            'AssertionError: 4 != 5\n'
        )
        result = _clean_traceback(tb)
        self.assertNotIn('/unittest/', result)
        self.assertIn('test_math.py', result)
        self.assertIn('AssertionError', result)

    def test_strips_rutlib_frames(self):
        tb = (
            'Traceback (most recent call last):\n'
            '  File "/home/user/src/rutlib/runner.py", line 50, in run\n'
            '    suite.run(result)\n'
            '  File "tests/test_io.py", line 8, in test_read\n'
            '    open("missing")\n'
            'FileNotFoundError: missing\n'
        )
        result = _clean_traceback(tb)
        self.assertNotIn('/rutlib/', result)
        self.assertIn('test_io.py', result)

    def test_preserves_all_when_all_internal(self):
        tb = (
            'Traceback (most recent call last):\n'
            '  File "/usr/lib/python3.12/unittest/case.py", line 123, in run\n'
            '    testMethod()\n'
            'RuntimeError: boom\n'
        )
        result = _clean_traceback(tb)
        self.assertIn('/unittest/', result)

    def test_passthrough_when_no_traceback(self):
        text = 'just a plain string with no frames\n'
        result = _clean_traceback(text)
        self.assertEqual(result, text)


class TestColorizeDiff(unittest.TestCase):
    def test_returns_text_object(self):
        tb = 'Traceback (most recent call last):\n  File "test.py", line 1\nAssertionError\n'
        result = _colorize_diff(tb)
        self.assertIsInstance(result, Text)

    def test_diff_lines_have_styles(self):
        diff = '- expected\n+ actual\n? ^\n'
        result = _colorize_diff(diff)
        plain = result.plain
        self.assertIn('- expected', plain)
        self.assertIn('+ actual', plain)
        # ? pointer line is consumed, not shown
        self.assertNotIn('? ^', plain)
        # Check that styles were applied (spans should be non-empty)
        self.assertTrue(len(result._spans) > 0)

    def test_pointer_highlights_chars(self):
        diff = '- hello world\n? ^\n+ hallo world\n? ^\n'
        result = _colorize_diff(diff)
        plain = result.plain
        # Both lines present, no ? lines
        self.assertIn('- hello world', plain)
        self.assertIn('+ hallo world', plain)
        self.assertNotIn('?', plain)
        # Multiple spans from per-char highlighting
        self.assertTrue(len(result._spans) > 2)

    def test_file_line_cyan(self):
        tb = 'File "/home/user/tests/test.py", line 1, in test_foo\n'
        result = _colorize_diff(tb)
        # Filename gets bold cyan, other parts get dim/yellow/cyan
        self.assertTrue(any('bold cyan' in str(s.style) for s in result._spans))

    def test_traceback_header_dropped(self):
        tb = 'Traceback (most recent call last):\n'
        result = _colorize_diff(tb)
        self.assertEqual(result.plain, '')

    def test_exception_line_bold_yellow(self):
        tb = 'AssertionError: 42 != 43\n'
        result = _colorize_diff(tb)
        self.assertIn('AssertionError', result.plain)
        self.assertTrue(any('bold yellow' in str(s.style) for s in result._spans))

    def test_code_line_unstyled(self):
        tb = '    self.assertEqual(a, b)\n'
        result = _colorize_diff(tb)
        self.assertIn('self.assertEqual(a, b)', result.plain)
        # Code lines are unstyled to differentiate from dim File line parts
        self.assertEqual(len(result._spans), 0)

    def test_diff_context_dim(self):
        tb = 'ValueError: bad\n  unchanged line\n'
        result = _colorize_diff(tb)
        self.assertIn('unchanged line', result.plain)
        self.assertTrue(any('dim' in str(s.style) for s in result._spans))

    def test_file_line_parts_styled(self):
        tb = '  File "/home/user/tests/test_foo.py", line 19, in test_bar\n'
        result = _colorize_diff(tb)
        plain = result.plain
        self.assertIn('test_foo.py', plain)
        self.assertIn(':19', plain)
        self.assertIn('in test_bar', plain)
        # No File " prefix or ", line " in new compact format
        self.assertNotIn('File "', plain)
        styles = [str(s.style) for s in result._spans]
        self.assertTrue(any('bold cyan' in s for s in styles))
        self.assertTrue(any('yellow' in s for s in styles))
        self.assertTrue(any(s == 'cyan' for s in styles))

    def test_prose_suppressed_when_diff_present(self):
        tb = (
            'AssertionError: Lists differ: [1, 2, 3] != [1, 2, 3, 4, 5]\n'
            'Second list contains 2 additional elements.\n'
            'First extra element 3:\n'
            '4\n'
            '- [1, 2, 3]\n'
            '+ [1, 2, 3, 4, 5]\n'
        )
        result = _colorize_diff(tb)
        self.assertNotIn('Second list contains', result.plain)
        self.assertNotIn('First extra element', result.plain)
        self.assertIn('- [1, 2, 3]', result.plain)
        self.assertIn('+ [1, 2, 3, 4, 5]', result.plain)

    def test_prose_kept_when_no_diff(self):
        tb = 'ValueError: something went wrong\nDetails here\n'
        result = _colorize_diff(tb)
        self.assertIn('Details here', result.plain)

    def test_prose_kept_when_verbose(self):
        tb = (
            'AssertionError: Lists differ: [1, 2, 3] != [1, 2, 3, 4, 5]\n'
            'Second list contains 2 additional elements.\n'
            '- [1, 2, 3]\n'
            '+ [1, 2, 3, 4, 5]\n'
        )
        result = _colorize_diff(tb, verbose=True)
        self.assertIn('Second list contains', result.plain)

    def test_traceback_header_kept_when_verbose(self):
        tb = 'Traceback (most recent call last):\n'
        result = _colorize_diff(tb, verbose=True)
        self.assertIn('Traceback', result.plain)
        self.assertTrue(any('dim' in str(s.style) for s in result._spans))


class TestTestHeader(unittest.TestCase):
    def test_contains_module_and_class_method(self):
        result = _test_header('test_math.TestCalc.test_add', 'FAIL', 80)
        plain = result.plain
        self.assertIn('test_math', plain)
        self.assertIn('TestCalc.test_add', plain)
        self.assertIn('FAIL', plain)

    def test_contains_error_label(self):
        result = _test_header('test_io.TestFile.test_read', 'ERROR', 80)
        plain = result.plain
        self.assertIn('ERROR', plain)

    def test_uses_dashes(self):
        result = _test_header('test_foo.TestBar.test_baz', 'FAIL', 80)
        self.assertIn('─', result.plain)

    def test_handles_deep_module_path(self):
        result = _test_header('pkg.sub.test_foo.TestBar.test_baz', 'FAIL', 80)
        plain = result.plain
        self.assertIn('test_foo', plain)
        self.assertIn('TestBar.test_baz', plain)


class TestDotMode(unittest.TestCase):
    class _Pass(unittest.TestCase):
        def test_pass(self):
            pass

    class _Fail(unittest.TestCase):
        def test_fail(self):
            self.fail("boom")

    def _make_result(self, verbose=False, total_tests=0):
        console = Console(file=StringIO(), width=80)
        result = RichTestResult(console, buffer=False, verbose=verbose)
        result._total_tests = total_tests
        return result, console

    def test_dot_on_success(self):
        result, console = self._make_result(verbose=False)
        test = self._Pass('test_pass')
        result.addSuccess(test)
        output = console.file.getvalue()
        self.assertIn('.', output)
        self.assertEqual(result._dot_count, 1)

    def test_dot_F_on_failure(self):
        result, console = self._make_result(verbose=False)
        test = self._Fail('test_fail')
        result.addFailure(test, (None, None, None))
        output = console.file.getvalue()
        self.assertIn('F', output)

    def test_dot_E_on_error(self):
        result, console = self._make_result(verbose=False)
        test = self._Pass('test_pass')
        result.addError(test, (None, None, None))
        output = console.file.getvalue()
        self.assertIn('E', output)

    def test_verbose_prints_full_line(self):
        result, console = self._make_result(verbose=True)
        test = self._Pass('test_pass')
        result.addSuccess(test)
        self.assertEqual(result._dot_count, 0)
        output = console.file.getvalue()
        self.assertIn('test_pass', output)

    def test_module_name_in_output(self):
        result, console = self._make_result(verbose=False)
        test = self._Pass('test_pass')
        result.addSuccess(test)
        result._flush_dots()
        output = console.file.getvalue()
        # Module name should appear before dots
        self.assertIn('test_output', output)

    def test_percentage_in_output(self):
        result, console = self._make_result(verbose=False, total_tests=2)
        test = self._Pass('test_pass')
        result.addSuccess(test)
        result.addSuccess(test)
        result._flush_dots()
        output = console.file.getvalue()
        self.assertIn('[100%]', output)

    def test_module_boundary_triggers_newline(self):
        """When a test from a different module arrives, the previous line is flushed."""
        console = Console(file=StringIO(), width=80)
        result = RichTestResult(console, buffer=False, verbose=False)
        result._total_tests = 2
        test1 = self._Pass('test_pass')
        result.addSuccess(test1)
        # Simulate a test from a different module
        test2 = self._Fail('test_fail')
        test2.__class__.__module__ = 'fake_other_module'
        result.addFailure(test2, (None, None, None))
        result._flush_dots()
        output = console.file.getvalue()
        # Both module names should appear on separate lines
        self.assertIn('test_output', output)
        self.assertIn('fake_other_module', output)


class TestFdCapturedOutput(unittest.TestCase):
    """Tests fd-capture through the real unittest lifecycle (buffer=True)."""

    def _run_suite(self, *test_classes):
        """Run test classes through RichTestRunner with buffer=True, return result and output."""
        console_buf = StringIO()
        runner = RichTestRunner(buffer=True)
        # Close the dup'd fd console before replacing it
        runner.console.file.close()
        runner.console = Console(file=console_buf, width=80, force_terminal=True)
        suite = unittest.TestSuite()
        for cls in test_classes:
            for name in unittest.TestLoader().getTestCaseNames(cls):
                suite.addTest(cls(name))
        result = runner.run(suite)
        return result, console_buf.getvalue()

    def test_subprocess_output_captured_on_failure(self):
        class _SubprocessFail(unittest.TestCase):
            def test_it(self):
                subprocess.run([sys.executable, "-c", "print('CAPTURED_HELLO')"])
                self.fail("boom")

        result, output = self._run_suite(_SubprocessFail)
        self.assertEqual(len(result.failures), 1)
        self.assertIn('Captured stdout (fd)', output)
        self.assertIn('CAPTURED_HELLO', output)

    def test_subprocess_stderr_captured_on_failure(self):
        class _StderrFail(unittest.TestCase):
            def test_it(self):
                subprocess.run([sys.executable, "-c",
                                "import sys; print('CAPTURED_ERR', file=sys.stderr)"])
                self.fail("boom")

        result, output = self._run_suite(_StderrFail)
        self.assertEqual(len(result.failures), 1)
        self.assertIn('Captured stderr (fd)', output)
        self.assertIn('CAPTURED_ERR', output)

    def test_no_capture_panel_on_success(self):
        class _Pass(unittest.TestCase):
            def test_it(self):
                subprocess.run([sys.executable, "-c", "print('SHOULD_NOT_APPEAR')"])

        result, output = self._run_suite(_Pass)
        self.assertTrue(result.wasSuccessful())
        self.assertNotIn('Captured stdout (fd)', output)
        self.assertNotIn('SHOULD_NOT_APPEAR', output)

    def test_passing_test_output_not_in_next_failure(self):
        class _Pass(unittest.TestCase):
            def test_a_pass(self):
                subprocess.run([sys.executable, "-c", "print('FROM_PASSING_TEST')"])

        class _Fail(unittest.TestCase):
            def test_b_fail(self):
                subprocess.run([sys.executable, "-c", "print('FROM_FAILING_TEST')"])
                self.fail("boom")

        result, output = self._run_suite(_Pass, _Fail)
        self.assertEqual(len(result.failures), 1)
        self.assertNotIn('FROM_PASSING_TEST', output)
        self.assertIn('FROM_FAILING_TEST', output)


class TestUptodateModulesDisplay(unittest.TestCase):
    """Tests for up-to-date modules display in dot vs verbose mode."""

    def _run_with_uptodate(self, uptodate_modules, verbose=False):
        buf = StringIO()
        runner = RichTestRunner(buffer=True, uptodate_modules=uptodate_modules, verbose=verbose)
        runner.console.file.close()
        runner.console = Console(file=buf, width=80)
        suite = unittest.TestSuite()
        runner.run(suite)
        return buf.getvalue()

    def test_dot_mode_single_summary_line(self):
        uptodate = {'test_foo': 10, 'test_bar': 20, 'test_baz': 5}
        output = self._run_with_uptodate(uptodate, verbose=False)
        self.assertIn('3 up-to-date (35 tests)', output)
        self.assertNotIn('test_foo', output)
        self.assertNotIn('test_bar', output)

    def test_verbose_per_module_lines(self):
        uptodate = {'test_foo': 10, 'test_bar': 20}
        output = self._run_with_uptodate(uptodate, verbose=True)
        self.assertIn('test_foo (10)', output)
        self.assertIn('test_bar (20)', output)

    def test_summary_includes_uptodate_count(self):
        uptodate = {'test_foo': 10, 'test_bar': 20}
        output = self._run_with_uptodate(uptodate)
        self.assertIn('30 up-to-date', output)

    def test_summary_no_uptodate_when_empty(self):
        output = self._run_with_uptodate({})
        self.assertNotIn('up-to-date', output)

    def test_summary_uptodate_dim_yellow(self):
        buf = StringIO()
        runner = RichTestRunner(buffer=True, uptodate_modules={'test_foo': 5})
        runner.console.file.close()
        runner.console = Console(file=buf, width=80, force_terminal=True)
        suite = unittest.TestSuite()
        runner.run(suite)
        output = buf.getvalue()
        self.assertIn('5 up-to-date', output)


class TestSummaryLine(unittest.TestCase):
    """Tests for the pytest-style summary line."""

    def _run_suite(self, *test_classes, uptodate_modules=None):
        buf = StringIO()
        runner = RichTestRunner(buffer=True, uptodate_modules=uptodate_modules)
        runner.console.file.close()
        runner.console = Console(file=buf, width=80, force_terminal=True)
        suite = unittest.TestSuite()
        for cls in test_classes:
            for name in unittest.TestLoader().getTestCaseNames(cls):
                suite.addTest(cls(name))
        result = runner.run(suite)
        return result, buf.getvalue()

    def test_all_passed(self):
        class _Pass(unittest.TestCase):
            def test_ok(self):
                pass
        _, output = self._run_suite(_Pass)
        self.assertIn('1 passed', output)
        self.assertNotIn('failed', output)
        self.assertIn('─', output)

    def test_failure_shows_failed_count(self):
        class _Fail(unittest.TestCase):
            def test_fail(self):
                self.fail("boom")
        _, output = self._run_suite(_Fail)
        self.assertIn('1 failed', output)

    def test_mixed_passed_and_failed(self):
        class _Pass(unittest.TestCase):
            def test_ok(self):
                pass
        class _Fail(unittest.TestCase):
            def test_fail(self):
                self.fail("boom")
        _, output = self._run_suite(_Pass, _Fail)
        self.assertIn('1 failed', output)
        self.assertIn('1 passed', output)

    def test_up_to_date_in_summary(self):
        _, output = self._run_suite(uptodate_modules={'test_foo': 10})
        self.assertIn('10 up-to-date', output)

    def test_time_in_summary(self):
        class _Pass(unittest.TestCase):
            def test_ok(self):
                pass
        _, output = self._run_suite(_Pass)
        self.assertRegex(output, r'in \d+\.\d+s')


class TestShortTestSummary(unittest.TestCase):
    """Tests for the short test summary section."""

    def _run_suite(self, *test_classes):
        buf = StringIO()
        runner = RichTestRunner(buffer=True)
        runner.console.file.close()
        runner.console = Console(file=buf, width=80, force_terminal=True)
        suite = unittest.TestSuite()
        for cls in test_classes:
            for name in unittest.TestLoader().getTestCaseNames(cls):
                suite.addTest(cls(name))
        runner.run(suite)
        return buf.getvalue()

    def test_shown_when_multiple_failures(self):
        class _Fail1(unittest.TestCase):
            def test_a(self):
                self.fail("first")
        class _Fail2(unittest.TestCase):
            def test_b(self):
                self.fail("second")
        output = self._run_suite(_Fail1, _Fail2)
        self.assertIn('SHORT TEST SUMMARY', output)
        self.assertIn('FAIL', output)

    def test_not_shown_when_single_failure(self):
        class _Fail(unittest.TestCase):
            def test_a(self):
                self.fail("only one")
        output = self._run_suite(_Fail)
        self.assertNotIn('SHORT TEST SUMMARY', output)

    def test_includes_exception_message(self):
        class _Fail1(unittest.TestCase):
            def test_a(self):
                self.assertEqual(1, 2)
        class _Fail2(unittest.TestCase):
            def test_b(self):
                self.assertEqual(3, 4)
        output = self._run_suite(_Fail1, _Fail2)
        self.assertIn('1 != 2', output)
        self.assertIn('3 != 4', output)
