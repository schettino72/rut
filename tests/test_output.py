import unittest
from rich.text import Text
from rutlib.output import _clean_traceback, _colorize_diff


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
        tb = 'File "test.py", line 1, in test_foo\n'
        result = _colorize_diff(tb)
        self.assertTrue(any('cyan' in str(s.style) for s in result._spans))

    def test_traceback_header_dim(self):
        tb = 'Traceback (most recent call last):\n'
        result = _colorize_diff(tb)
        self.assertTrue(any('dim' in str(s.style) for s in result._spans))
