import sys
import logging
from pathlib import Path

import click
from rich.logging import RichHandler

from .collect import collect_paths
from .runner import Runner


log = logging.getLogger('rut')

@click.command()
# logging
# @click.option('--log-level', help='logging level', )
# @click.option('--log-file', )
# @click.option('--log-show', help='show logs on stdout')
# collection
# reporting
@click.argument('specs', nargs=-1, metavar='TESTS')
def main(specs):
    """run unittest tests

    TESTS: python package in dot-notation
    """
    # logging.basicConfig(filename='rut.log', filemode='w', level=logging.INFO)
    logging.basicConfig(
        level=logging.INFO,
        format="[cyan]%(name)s[/cyan] %(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(markup=True)])


    # add current dir - with lowest priority.
    log.info("Adding path to sys.path: '%s'." % Path.cwd())
    sys.path.append(str(Path.cwd()))

    collector = collect_paths(specs)
    runner = Runner()
    runner.execute(collector)

