import os
import sys
import shutil
import coverage
from .cli import RutCLI
from .runner import RutRunner


def main():
    sys.path.insert(0, os.getcwd())
    os.environ['TEST_RUNNER'] = 'rut'
    cli = RutCLI()

    if cli.args.cov:
        cov = coverage.Coverage(source=cli.coverage_source)
        cov.start()

    runner = RutRunner(
        test_path=cli.args.test_path or cli.test_base_dir,
        test_base_dir=cli.test_base_dir,
        keyword=cli.args.keyword,
        failfast=cli.args.exitfirst,
        capture=cli.args.capture,
        warning_filters=cli.warning_filters(cli.config.get("warning_filters", [])),
    )
    suite = runner.load_tests()
    result = runner.run_tests(suite)

    if cli.args.cov:
        cov.stop()
        cov.save()
        cov.report(show_missing=True)

    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    if 'PYTHONBREAKPOINT' not in os.environ and shutil.which('ipdb'):
        os.environ['PYTHONBREAKPOINT'] = 'ipdb.set_trace'
    main()
