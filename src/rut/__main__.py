import logging
import asyncio

import click
from rich.logging import RichHandler

from rut.collect import Collector
from rut.ctl import single_worker, mp_master, mp_worker


log = logging.getLogger('rut')

@click.command()
# logging
# @click.option('--log-level', help='logging level', )
# @click.option('--log-file', )
@click.option('--log-show', default=False, is_flag=True,
              help='show logs on stdout/terminal')
# reporting
# capture
@click.option('--capture', 'capture', default='sys', type=click.Choice(['sys', 'no']),
              help='capture of test stdout/stderr')
@click.option('-s', 'capture_no', default=False, is_flag=True)
# runner
@click.option('-x', '--exitfirst', default=False, is_flag=True,
              help='exit instantly on first error or failed test.')
# worker
@click.option('-n', 'num_proc', default=0,
              help='number of child worker processes')
@click.option('--worker', 'is_worker', default=False, is_flag=True,
              help='run tests as worker, output as msgpack')
@click.option('--imp', help='import spec <pkg>|<path> i.e. "tests|tests/__init__.py"')
# collection / selection
@click.argument('args', nargs=-1, metavar='TESTS')
def main(args, log_show,
         capture, capture_no, exitfirst,
         num_proc, is_worker, imp):
    """run unittest tests

    args: python pkg/module paths
    """
    # logging.basicConfig(filename='rut.log', filemode='w', level=logging.INFO)
    if log_show:
        logging.basicConfig(
            level=logging.INFO,
            format="[cyan]%(name)s[/cyan] %(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(markup=True)])

    if is_worker:
        return mp_worker(imp)

    if capture_no:
        capture = 'no'
    collector = Collector()
    collector.process_args(args)
    if num_proc:
        return asyncio.run(mp_master(collector, num_proc))
    return single_worker(collector, capture=capture, exitfirst=exitfirst)

if __name__ == '__main__':
    main()
