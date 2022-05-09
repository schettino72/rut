import logging
import inspect
from pathlib import Path
import importlib
import pkgutil
from types import ModuleType
from functools import singledispatch

import msgpack
from rich import traceback as rich_tb
from rich.pretty import Node as RichNode

from .checker import TestFailure


log = logging.getLogger(__name__)


class FailureInfo:
    def __init__(self, name, args, stack):
        self.name = name
        self.args = args
        self.stack = stack

    @classmethod
    def from_exception(cls, exc: TestFailure):
        stack = []
        tb = exc.__traceback__
        while tb:
            frame = tb.tb_frame
            tb = tb.tb_next
            if frame.f_globals['__package__'] == 'rut':
                continue
            code = frame.f_code
            stack.append({
                'filename': code.co_filename,
                'module': frame.f_globals['__name__'],
                'name': code.co_name,
                'lineno': frame.f_lineno,
                'firstlineno': code.co_firstlineno,
            })
        return cls(exc.__class__.__name__, exc.args, stack)

class ExceptionInfo:
    def __init__(self, exc_type, value, trace):
        self.exc_type = exc_type
        self.value = value
        # rich's internal dataclass with traceback info
        self.trace = trace

    @classmethod
    def from_exception(cls, exc_info) :
        exc_type = exc_info[0].__name__
        value = exc_info[1]
        # FIXME: locals include way more info then it should rich.pretty.Node
        # FIXME: extract should support max_depth
        trace: rich_tb.Trace = rich_tb.Traceback.extract(*exc_info, show_locals=True)
        return cls(exc_type, value, trace)


from rich import inspect as rich_inspect


def default_packer(obj):
    # print('PP', type(obj), obj.__dict__)
    return obj.__dict__

class CaseOutcome:
    def __init__(self):
        # exec-phase
        self.result = None  # SUCCESS, FAIL, ERROR
        self.io_out = None  # never set if success
        self.failure = None  # FailureInfo
        self.exc_info = None  # ExceptionInfo

    def pack(self):
        raw = {
            'r': self.result,
            'o': self.io_out,
            'f': self.failure,
            'e': self.exc_info,
        }
        return msgpack.packb(raw, default=default_packer)

    @classmethod
    def _unpack_local_children(cls, raw_children) -> dict[str, RichNode]:
        result = []
        for raw_node in raw_children:
            child_children = raw_node.pop('children')
            node = RichNode(**raw_node)
            if child_children:
                node.children = cls._unpack_local_children(rawchildren)
            result.append(node)
        return result

    @classmethod
    def unpack(cls, msg):
        case = CaseOutcome()
        raw = msgpack.unpackb(msg)
        case.result = raw['r']
        case.io_out = raw['o']
        if raw['f']:
            case.failure = FailureInfo(**raw['f'])
        else:
            case.failure = None
        if raw['e']:
            stacks = []
            for stack_raw in raw['e']['trace']['stacks']:
                frames = []
                for frame_raw in stack_raw.pop('frames'):
                    f_locals = {}
                    raw_locals = frame_raw.pop('locals')
                    for name, raw_node in raw_locals.items():
                        raw_children = raw_node.pop('children')
                        node = RichNode(**raw_node)
                        if raw_children:
                            node.children = cls._unpack_local_children(raw_children)
                        f_locals[name] = node
                    frames.append(rich_tb.Frame(**frame_raw, locals=f_locals))
                stacks.append(rich_tb.Stack(frames=frames, **stack_raw))
            trace = rich_tb.Trace(stacks)
            case.exc_info = ExceptionInfo(raw['e']['exc_type'], raw['e']['value'], trace)
        else:
            case.exc_info = None
        return case


class TestCase:
    def __init__(self, func, cls=None):
        """
        """
        # load-phase
        self.cls = cls
        self.func = func


class Collector:
    """
    1) find/load python modules
    2) collect tests from module
    3) select which tests cases will be executed
    """
    def __init__(self):
        self.mods = []  # list of module name in dot notation i.e. `<pkg>.<name>`
        self.cases = {}  # mod_name: {test_name, TestCase}


    def find_pkg_modules(self, name: str):
        # module = importlib.import_module(name)
        mod_spec: importlib.machinery.ModuleSpec = importlib.util.find_spec(name)
        if mod_spec.parent == mod_spec.name:  # is package
            for info in pkgutil.walk_packages(mod_spec.submodule_search_locations):
                if info.name.startswith('test_'):
                    self.mods.append(f'{name}.{info.name}')
        else:
            self.mods.append(name)

    @classmethod
    def _collect_module_tests(cls, module: ModuleType):
        """get test functions (test_) from module given by path."""
        tests = {}

        # load functions
        for name, ref in inspect.getmembers(module, inspect.isfunction):
            if name.startswith('test_'):
                tests[ref.__qualname__] = TestCase(ref)

        # load class methods
        for cls_name, cls_ref in inspect.getmembers(module, inspect.isclass):
            if cls_name.startswith('Test'):
                for name, ref in inspect.getmembers(cls_ref, inspect.isfunction):
                    if name.startswith('test_'):
                        tests[ref.__qualname__]  = TestCase(ref, cls=cls_ref)
        return tests


    def collect_cases(self):
        for mod_name in self.mods:
            log.info('load: %s' % mod_name)
            module = importlib.import_module(mod_name)
            self.cases[mod_name] = self._collect_module_tests(module)


    # TODO: create a selector class
    def iter_cases(self):
        for mod_name, cases in sorted(self.cases.items()):
            for case in sorted(cases.values(), key=lambda c: c.func.__code__.co_firstlineno):
                yield mod_name, case.func.__qualname__, case




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
        for spec in specs:
            collector.find_pkg_modules(spec)

    # collected all tests from found modules
    collector.collect_cases()
    return collector
