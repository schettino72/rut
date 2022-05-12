import sys

import tempfile
from importlib import util as imp_util


def add_test_cases(selector, src, name='this_test'):
    """create module from src text, and add its TestCase's to collector"""

    with tempfile.NamedTemporaryFile(suffix='.py') as tmp:
        tmp.write(src.encode())
        tmp.flush()

        spec = imp_util.spec_from_file_location('tmp', tmp.name)
        module = imp_util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules['tmp'] = module

        selector.mods.append(name)
        selector.cases[name] = selector._collect_module_tests(module)
        return module

