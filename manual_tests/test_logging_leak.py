"""
Test file to reproduce logging output leaking through stdout capture.

Run with: uv run rut tests/samples/test_logging_leak.py

Expected: logging output should NOT appear when capture is enabled (default)
Actual: logging output leaks to stderr even with capture enabled
"""
import logging
import unittest

logging.basicConfig(level=logging.INFO)


class TestLoggingLeak(unittest.TestCase):
    def test_passing_with_logging(self):
        """This test passes but logs a message - should be silent with capture."""
        logging.info("LOG FROM PASSING TEST - this should NOT appear with capture")
        self.assertTrue(True)

    def test_failing_with_logging(self):
        """This test fails and logs - log should appear in failure output only."""
        logging.info("LOG FROM FAILING TEST - should appear in failure output")
        self.fail("Intentional failure")
