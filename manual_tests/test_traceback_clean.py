"""Manual test: clean traceback output.

Run with:
    rut manual_tests/test_traceback_clean.py

Expected: panels show only user code frames.
  - No /unittest/case.py or /rutlib/ frames visible.
  - File lines in cyan, Traceback header in dim.
  - When all frames are internal (setUp error), full traceback preserved.
"""
import unittest


# -- helpers to create deep tracebacks --
def _level3():
    raise RuntimeError("deep error in app code")

def _level2():
    _level3()

def _level1():
    _level2()


class TestDeepTraceback(unittest.TestCase):

    def test_three_level_deep(self):
        """Should show 3 user frames: _level1 -> _level2 -> _level3."""
        _level1()


class TestSimpleAssertion(unittest.TestCase):

    def test_assertEqual_no_diff(self):
        """Should show only test file frame, no unittest internals."""
        self.assertEqual(4, 5)

    def test_unhandled_exception(self):
        """ValueError — not an assertion, still clean traceback."""
        int("not_a_number")


class TestSetUpError(unittest.TestCase):

    def setUp(self):
        raise RuntimeError("setUp exploded")

    def test_never_reached(self):
        """Error in setUp — all frames are internal, should show full traceback."""
        pass
