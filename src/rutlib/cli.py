import os
import sys
import shutil
import tomllib
import coverage
from .runner import RutCLI


def main():
    os.environ['TEST_RUNNER'] = 'rut'
    cli = RutCLI()

    if cli.args.cov:
        # Default coverage source
        cov_source = ["src", "tests"]
        try:
            with open("pyproject.toml", "rb") as f:
                pyproject_data = tomllib.load(f)
                rut_config = pyproject_data.get("tool", {}).get("rut", {})
                if "coverage_source" in rut_config:
                    cov_source = rut_config["coverage_source"]
        except FileNotFoundError:
            pass  # No pyproject.toml, use default

        # Check for non-existent source directories
        for source_dir in cov_source:
            if not os.path.isdir(source_dir):
                print(
                    f"Warning: coverage source directory '{source_dir}' does not exist.",
                    file=sys.stderr,
                )

        cov = coverage.Coverage(source=cov_source)
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
