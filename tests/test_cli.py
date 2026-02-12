import pathlib
import unittest
from types import SimpleNamespace
from unittest.mock import patch, mock_open
from io import StringIO
from rutlib.cli import RutCLI


class TestCLI(unittest.TestCase):
    def test_warning_filters(self):
        cli = RutCLI()
        filters = cli.warning_filters([
            "error:message:UserWarning:tests.samples.my_specific_module",
            "always:message:DeprecationWarning",
        ])
        self.assertEqual(len(filters), 2)
        self.assertEqual(filters[0]['action'], 'error')
        self.assertEqual(filters[0]['category'], UserWarning)
        self.assertEqual(filters[0]['module'], 'tests.samples.my_specific_module')
        self.assertEqual(filters[1]['action'], 'always')
        self.assertEqual(filters[1]['category'], DeprecationWarning)
        self.assertEqual(filters[1]['module'], '')

    def test_source_dirs_from_config(self):
        cli = RutCLI()
        cli.parse_args([])
        cli.setup()
        # source_dirs are now absolute paths
        self.assertTrue(any("tests" in d for d in cli.source_dirs))

    def test_source_dirs_error_on_missing_with_cov(self):
        cli = RutCLI()
        cli.project_root = pathlib.Path.cwd()
        cli.config = {"source_dirs": ["non_existent_dir"]}
        cli.args = SimpleNamespace(cov=True, changed=False)
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                cli._resolve_source_dirs()
            self.assertIn("non_existent_dir", mock_stderr.getvalue())

    def test_source_dirs_error_on_partial_missing_with_changed(self):
        cli = RutCLI()
        cli.project_root = pathlib.Path.cwd()
        cli.config = {"source_dirs": ["tests", "non_existent_dir"]}
        cli.args = SimpleNamespace(cov=False, changed=True)
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                cli._resolve_source_dirs()
            self.assertIn("non_existent_dir", mock_stderr.getvalue())

    def test_source_dirs_no_error_without_cov_or_changed(self):
        cli = RutCLI()
        cli.project_root = pathlib.Path.cwd()
        cli.config = {"source_dirs": ["non_existent_dir"]}
        cli.args = SimpleNamespace(cov=False, changed=False)
        dirs = cli._resolve_source_dirs()
        self.assertEqual(len(dirs), 1)

    def test_source_dirs_defaults_to_dot_without_config(self):
        cli = RutCLI()
        cli.project_root = pathlib.Path.cwd()
        cli.config = {}
        cli.args = SimpleNamespace(cov=False, changed=False)
        dirs = cli._resolve_source_dirs()
        self.assertEqual(dirs, ["."])

    def test_test_dir_error_on_missing(self):
        cli = RutCLI()
        cli.project_root = pathlib.Path.cwd()
        cli.args = SimpleNamespace(test_base_dir=None)
        cli.config = {"test_base_dir": "non_existent_tests"}
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit):
                cli._resolve_test_dir()
            self.assertIn("non_existent_tests", mock_stderr.getvalue())

    def test_test_dir_from_explicit_arg(self):
        cli = RutCLI()
        cli.parse_args(['--test-base-dir', 'tests/samples'])
        cli.setup()
        self.assertEqual(cli.test_dir, "tests/samples")

    def test_test_dir_not_affected_by_positional(self):
        cli = RutCLI()
        cli.parse_args(['some/other/path'])
        cli.setup()
        self.assertTrue(cli.test_dir.endswith("tests"))

    def test_test_dir_defaults_to_dot_without_config(self):
        cli = RutCLI()
        cli.project_root = pathlib.Path.cwd()
        cli.args = SimpleNamespace(test_base_dir=None)
        cli.config = {}
        test_dir = cli._resolve_test_dir()
        self.assertEqual(test_dir, str(pathlib.Path.cwd()))

    def test_load_config_warns_no_pyproject(self):
        cli = RutCLI()
        with patch('pathlib.Path.is_file', return_value=False):
            config = cli.load_config()
        self.assertEqual(config, {})
        self.assertEqual(cli.project_root, pathlib.Path.cwd())

    def test_load_config_warns_no_rut_section(self):
        cli = RutCLI()
        toml_data = b'[project]\nname = "foo"\n'
        with patch('builtins.open', mock_open(read_data=toml_data)):
            config = cli.load_config()
        self.assertEqual(config, {})
