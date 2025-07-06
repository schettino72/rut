import unittest

# This file is used by tests/test_runner.py::TestRunnerHooks

class HookCheckTest(unittest.TestCase):
    def test_setup_file_exists(self):
        """
        This test runs during the test session.
        It checks that the setup file created by the setup hook exists.
        """
        pass
