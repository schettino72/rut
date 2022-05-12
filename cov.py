import sys

from click.core import Context
from coverage import Coverage


def cov_wrapper(args):
    if not args:
        source = ['rut', 'tests']
    else:
        source = []
        for mod in args:
            # len('test_')==5   len('.py')==3
            fname = mod.split('/')[-1][:-3]
            source.append(f'tests.{fname}')
            source.append(f'rut.{fname[5:]}')

    cov = Coverage(source=source, omit=['tests/sample_proj/*'])
    cov.erase()
    cov.start()

    from rut.collect import Collector
    from rut.__main__ import single_worker
    collector = Collector()
    collector.process_args(args)
    single_worker(collector, False)

    cov.stop()
    cov.save()
    cov.report(show_missing=True)


if __name__ == '__main__':
    cov_wrapper(sys.argv[1:])
