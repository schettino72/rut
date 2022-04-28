import importlib
import inspect


class Runner:
    def __init__(self):
        self.tests = {}  # name -> {func, result}

    def load_tests(self, path):
        """get test functions (test_) from module given by path."""
        assert path.suffix == '.py'
        module_name = '.'.join(path.parts)[:-3]
        print('loading...', path)
        module = importlib.import_module(module_name)
        for name, ref in inspect.getmembers(module):
            if name.startswith('test_'):
                self.tests[name] = {'func': ref}

    def execute(self):
        """execute tests"""
        for name, test in self.tests.items():
            try:
                test['func']()
            except Exception:
                result = 'ERROR'
            else:
                result = 'PASS'
            test['result'] = result
            print(f"{name}: {result}")
