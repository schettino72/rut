import unittest
import os
import sys
import io
from unittest.mock import patch, MagicMock

from rutlib.cli import main

class TestCLI(unittest.TestCase):
    def setUp(self):
        self.original_argv = sys.argv
        self.original_exit = sys.exit
        sys.exit = MagicMock()
        self.original_cwd = os.getcwd()

    def tearDown(self):
        sys.argv = self.original_argv
        sys.exit = self.original_exit
        os.chdir(self.original_cwd)

    @patch('rutlib.cli.RutCLI')
    @patch('rutlib.cli.coverage.Coverage')
    def test_coverage_source_from_config(self, mock_coverage, mock_rut_cli):
        # Change to the directory with the sample pyproject.toml
        os.chdir("tests/samples/config")

        # Mock the CLI args and run the main function
        sys.argv = ["rut", "--cov"]
        main()

        # Check that coverage was called with the correct source
        mock_coverage.assert_called_with(source=["my_app"])

    @patch('rutlib.cli.RutCLI')
    @patch('rutlib.cli.coverage.Coverage')
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_warns_on_missing_coverage_source(self, mock_stderr, mock_coverage, mock_rut_cli):
        # Change to the directory with the sample pyproject.toml
        os.chdir("tests/samples/config")

        # Mock the CLI args and run the main function
        sys.argv = ["rut", "--cov"]
        main()

        # Check that the warning was printed to stderr
        self.assertIn("Warning: coverage source directory 'my_app' does not exist.", mock_stderr.getvalue())

if __name__ == '__main__':
    unittest.main()