import logging

import click
from rich.logging import RichHandler

from .collect import Collector, Selector
from .runner import Runner, Reporter


log = logging.getLogger('rut')

@click.command()
# logging
# @click.option('--log-level', help='logging level', )
# @click.option('--log-file', )
@click.option('--log-show', default=False, is_flag=True,
              help='show logs on stdout/terminal')
# collection
# reporting
# runner
@click.option('-x', '--exitfirst', default=False, is_flag=True,
              help='exit instantly on first error or failed test.')
@click.option('--worker', default=False, is_flag=True,
              help='run tests as worker, output as msgpack')
@click.argument('args', nargs=-1, metavar='TESTS')
def main(args, log_show, exitfirst, worker):
    """run unittest tests

    TESTS: python package in dot-notation
    """
    # logging.basicConfig(filename='rut.log', filemode='w', level=logging.INFO)
    if log_show:
        logging.basicConfig(
            level=logging.INFO,
            format="[cyan]%(name)s[/cyan] %(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(markup=True)])

    collector = Collector()
    collector.process_args(args)

    selector = Selector(collector.mods)
    reporter = Reporter()
    runner = Runner()

    for outcome in runner.execute(selector):
        reporter.handle_outcome(outcome)
        if exitfirst and outcome.result in ('ERROR', 'FAIL'):
            break

if __name__ == '__main__':
    main()
