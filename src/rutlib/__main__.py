import os
import sys
import shutil
import coverage
from .cache import update_cache
from .cli import RutCLI, RichTestRunner
from .runner import RutRunner


def should_update_cache(result, keyword) -> bool:
    """Determine if cache should be updated after test run.

    Cache is updated only when:
    - Tests passed
    - At least one test ran
    - No -k filter was used (partial runs shouldn't update cache)
    """
    return result.wasSuccessful() and result.testsRun > 0 and not keyword


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
        alpha=cli.args.alpha,
        source_dirs=cli.coverage_source,
        verbose=cli.args.verbose,
        changed=cli.args.changed,
    )
    suite = runner.load_tests()

    if cli.args.dry_run:
        print(f"Would run {suite.countTestCases()} tests:")
        for test in suite:
            print(f"  {test.id()}")
        sys.exit(0)

    runner_class = RichTestRunner if not cli.args.no_color else None
    result = runner.run_tests(suite, runner_class=runner_class)

    if cli.args.cov:
        cov.stop()
        cov.save()
        cov.report(show_missing=True)

    if result.wasSuccessful():
        if should_update_cache(result, cli.args.keyword):
            update_cache(cli.coverage_source)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    if 'PYTHONBREAKPOINT' not in os.environ and shutil.which('ipdb'):
        os.environ['PYTHONBREAKPOINT'] = 'ipdb.set_trace'
    main()