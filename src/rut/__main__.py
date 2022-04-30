import sys
import logging
from pathlib import Path

import click
from rich.logging import RichHandler

from .collect import collect_paths
from .runner import Runner


log = logging.getLogger(__name__)

@click.command()
# logging
# @click.option('--log-level', help='logging level', )
# @click.option('--log-file', )
# @click.option('--log-show', help='show logs on stdout')
# collection
# reporting
@click.argument('paths', nargs=-1, metavar='PKG_MOD')
def main(paths):
    """run unittest tests

    TEST_PATHS: paths to dir package/module
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

    collector = collect_paths(paths)
    runner = Runner()
    runner.execute(collector)

