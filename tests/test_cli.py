import unittest
import os
import sys
import io
from unittest.mock import patch, MagicMock, PropertyMock

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
        # Mock the coverage_source property
        type(mock_rut_cli.return_value).coverage_source = PropertyMock(return_value=["my_app"])

        # Mock the CLI args and run the main function
        sys.argv = ["rut", "--cov", os.path.join(self.original_cwd, "tests")]
        main()

        # Check that coverage was called with the correct source
        mock_coverage.assert_called_with(source=["my_app"])

    def test_warns_on_missing_coverage_source(self):
        # Change to the directory with the sample pyproject.toml
        os.chdir("tests/samples/config")

        # Redirect stderr
        original_stderr = sys.stderr
        sys.stderr = captured_stderr = io.StringIO()

        with patch('rutlib.cli.coverage.Coverage'):
            # Mock the CLI args and run the main function
            sys.argv = ["rut", "--cov", os.path.join(self.original_cwd, "tests")]
            main()

        # Restore stderr
        sys.stderr = original_stderr

        # Check that the warning was printed to stderr
        self.assertIn("Warning: coverage source directory 'my_app' does not exist.", captured_stderr.getvalue())

if __name__ == '__main__':
    unittest.main()
