import unittest
from rich.text import Text
from rutlib.output import _clean_traceback, _colorize_diff, _test_header


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

    def test_code_line_dim(self):
        tb = '    self.assertEqual(a, b)\n'
        result = _colorize_diff(tb)
        self.assertIn('self.assertEqual(a, b)', result.plain)
        self.assertTrue(any('dim' in str(s.style) for s in result._spans))

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
        self.assertIn('19', plain)
        self.assertIn('test_bar', plain)
        styles = [str(s.style) for s in result._spans]
        self.assertTrue(any('bold cyan' in s for s in styles))
        self.assertTrue(any('yellow' in s for s in styles))
        self.assertTrue(any(s == 'cyan' for s in styles))


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
