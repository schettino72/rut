import unittest
from unittest.mock import patch
from io import StringIO
from rutlib.cli import RutCLI

class TestCLI(unittest.TestCase):
    def test_warning_filters(self):
        with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
            mock_parse_args.return_value = unittest.mock.Mock(
                keyword=None, exitfirst=False, capture=False, cov=False, test_path='tests'
            )
            cli = RutCLI()
            cli.config = {
                "warning_filters": [
                    "error:message:UserWarning:tests.samples.my_specific_module",
                    "always:message:DeprecationWarning",
                ]
            }
            filters = cli.warning_filters(cli.config.get("warning_filters", []))
            self.assertEqual(len(filters), 2)
            self.assertEqual(filters[0]['action'], 'error')
            self.assertEqual(filters[0]['category'], UserWarning)
            self.assertEqual(filters[0]['module'], 'tests.samples.my_specific_module')
            self.assertEqual(filters[1]['action'], 'always')
            self.assertEqual(filters[1]['category'], DeprecationWarning)
            self.assertEqual(filters[1]['module'], '')

    def test_coverage_source_from_config(self):
        with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
            mock_parse_args.return_value = unittest.mock.Mock(
                keyword=None, exitfirst=False, capture=False, cov=False, test_path='tests'
            )
            cli = RutCLI()
            cli.config = {"coverage_source": ["source1", "source2"]}
            self.assertEqual(cli.coverage_source, ["source1", "source2"])

    def test_warns_on_missing_coverage_source(self):
        with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
            mock_parse_args.return_value = unittest.mock.Mock(
                keyword=None, exitfirst=False, capture=False, cov=False, test_path='tests'
            )
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                cli = RutCLI()
                cli.config = {"coverage_source": ["non_existent_dir"]}
                self.assertEqual(cli.coverage_source, ["non_existent_dir"])
                self.assertIn("Warning: coverage source directory 'non_existent_dir' does not exist.", mock_stderr.getvalue())