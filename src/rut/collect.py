import logging
import inspect
from pathlib import Path
import importlib
import pkgutil


log = logging.getLogger(__name__)

class Collector:
    """Collect tests in 2 steps:
    1) find/load python modules
    2) collect tests from module
    """
    def __init__(self):
        self.mods = []  # list of module name in dot notation i.e. `<pkg>.<name>`
        self.tests = {}


    def find_pkg_modules(self, path: str):
        for info in pkgutil.walk_packages([path]):
            if info.name.startswith('test_'):
                self.mods.append(f'{path}.{info.name}')


    @classmethod
    def _collect_module_tests(cls, mod_name: str):
        """get test functions (test_) from module given by path."""
        tests = {}
        log.info('load: %s' % mod_name)
        module = importlib.import_module(mod_name)

        # load functions
        for name, ref in inspect.getmembers(module, inspect.isfunction):
            if name.startswith('test_'):
                tests[ref.__qualname__] = {'func': ref}

        # load class methods
        for cls_name, cls_ref in inspect.getmembers(module, inspect.isclass):
            if cls_name.startswith('Test'):
                for name, ref in inspect.getmembers(cls_ref, inspect.isfunction):
                    if name.startswith('test_'):
                        tests[ref.__qualname__] = {
                            'cls': cls_ref,
                            'func': ref,
                        }
        return tests


    def collect_tests(self):
        for mod_name in self.mods:
            self.tests.update(self._collect_module_tests(mod_name))




def collect_paths(specs):
    """return Collector
    """
    collector = Collector()

    # no args specified, search on default paths
    if len(specs) == 0:
        # 1) tests
        test_dir = Path('tests')
        if test_dir.exists():
            collector.find_pkg_modules(str(test_dir))
        else:
            raise NotImplementedError('check src or local')
    # process CLI / config test spec with paths
    else:
        raise NotImplementedError('put your tests in "tests" folder.')

    # collected all tests from found modules
    collector.collect_tests()
    return collector
