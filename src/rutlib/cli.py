import os
import sys
import shutil
import coverage
from .runner import RutCLI


def main():
    os.environ['TEST_RUNNER'] = 'rut'
    cli = RutCLI()

    if cli.args.cov:
        cov = coverage.Coverage(source=cli.coverage_source)
        cov.start()

    suite = cli.load_tests()
    result = cli.run_tests(suite)

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