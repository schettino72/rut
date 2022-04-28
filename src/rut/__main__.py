import sys
from pathlib import Path

from . import Runner


def main():
    sys.path.append(str(Path.cwd()))

    runner = Runner()
    for fn in sys.argv[1:]:
        runner.load_tests(Path(fn))
    runner.execute()


if __name__ == '__main__':
    main()
