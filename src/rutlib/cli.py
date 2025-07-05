import coverage
from .runner import RutCLI

def main():
    cli = RutCLI()
    suite = cli.load_tests()

    if cli.args.cov:
        cov = coverage.Coverage(source=["src"])
        cov.start()

    cli.run_tests(suite)

    if cli.args.cov:
        cov.stop()
        cov.save()
        cov.report()

if __name__ == "__main__":
    main()
