import sys
from pathlib import Path

import click

from .collect import collect_paths
from .runner import Runner



@click.command()
@click.argument('paths', nargs=-1, metavar='PKG_MOD')
def main(paths):
    """run unittest tests

    TEST_PATHS: paths to dir package/module
    """
    # add current dir - with lowest priority.
    sys.path.append(str(Path.cwd()))

    collector = collect_paths(paths)
    runner = Runner()
    runner.execute(collector)


if __name__ == '__main__':
    main()
