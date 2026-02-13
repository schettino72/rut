"""Manual test for fd-level output capture.

Run:
    rut manual_tests/test_output_leak.py

Passing tests: no output should leak between dots/checkmarks.
Failing test: captured fd output should appear in the failure report.
"""
import subprocess
import sys
import unittest


class TestOutputLeak(unittest.TestCase):
    def test_print_stdout(self):
        """print() goes to sys.stdout — should be captured by buffer."""
        print("LEAK_VIA_PRINT: this should NOT appear")
        self.assertTrue(True)

    def test_write_dunder_stdout(self):
        """sys.__stdout__ bypasses unittest buffer — leaks to terminal."""
        sys.__stdout__.write("LEAK_VIA___STDOUT__: this WILL appear\n")
        sys.__stdout__.flush()
        self.assertTrue(True)

    def test_subprocess(self):
        """Subprocess inherits fds — leaks to terminal."""
        subprocess.run([sys.executable, "-c", "print('LEAK_VIA_SUBPROCESS: this WILL appear')"])
        self.assertTrue(True)

    def test_cached_stdout_ref(self):
        """Simulates code that cached stdout before unittest redirected it."""
        # This is what happens when a module-level variable holds sys.stdout
        # and later writes to it during a test
        original = sys.__stdout__
        original.write("LEAK_VIA_CACHED_REF: this WILL appear\n")
        original.flush()
        self.assertTrue(True)

    def test_fd_output_shown_on_failure(self):
        """Failing test with subprocess output — captured fd output should appear in report."""
        subprocess.run([sys.executable, "-c", "print('FD_STDOUT: visible in failure report')"])
        subprocess.run([sys.executable, "-c", "import sys; print('FD_STDERR: visible too', file=sys.stderr)"])
        self.fail("intentional failure to verify fd capture is shown")
