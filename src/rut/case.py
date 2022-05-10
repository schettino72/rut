"""
 - TestCase: Wrapper around collected test functions
 - CaseOutcome: outcome of TestCase Execution
 - FailureInfo: information of TestFailure check()
 - ErrorInfo: information of exception + traceback
"""

from __future__ import annotations
from types import TracebackType
from typing import Optional, Any, Type, NewType

import msgpack  # type: ignore
from rich.pretty import Node as RichNode
from rich import traceback as rich_tb

from .checker import TestFailure


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

ExceptionInfo = NewType('ExceptionInfo',
                        tuple[Type[BaseException], BaseException, TracebackType])

class ErrorInfo:
    def __init__(self, exc_type, value, trace):
        self.exc_type: str = exc_type
        self.value: Any = value
        # rich's internal dataclass with traceback info
        self.trace: rich_tb.Trace = trace

    @classmethod
    def from_exception(cls, exc_info: ExceptionInfo) -> 'ErrorInfo':
        exc_type = exc_info[0].__class__.__name__
        value = exc_info[1]
        # FIXME: locals include way more info then it should rich.pretty.Node
        # FIXME: extract should support max_depth
        trace: rich_tb.Trace = rich_tb.Traceback.extract(
            exc_info[0], exc_info[1], exc_info[2], show_locals=True)
        return cls(exc_type, value, trace)



class MsgpackMixin:
    """Helper to serialize CaseOutcome for IPC"""

    @staticmethod
    def default_packer(obj):
        # print('PP', type(obj), obj.__dict__)
        return obj.__dict__

    def pack(self):
        raw = {
            'm': self.mod_name,
            'c': self.case_name,
            'r': self.result,
            'o': self.io_out,
            'f': self.failure,
            'e': self.error,
        }
        return msgpack.packb(raw, default=self.default_packer)

    @classmethod
    def _unpack_local_children(cls, raw_children) -> list[RichNode]:
        result = []
        for raw_node in raw_children:
            child_children = raw_node.pop('children')
            node = RichNode(**raw_node)
            if child_children:
                node.children = cls._unpack_local_children(child_children)
            result.append(node)
        return result

    @classmethod
    def from_data(cls, raw):
        case = CaseOutcome(raw['m'], raw['c'])
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
            case.error = ErrorInfo(raw['e']['exc_type'], raw['e']['value'], trace)
        else:
            case.error = None
        return case

    @classmethod
    def unpack(cls, msg):
        raw = msgpack.unpackb(msg)
        return cls.from_data(raw)


class CaseOutcome(MsgpackMixin):
    def __init__(self, mod_name, case_name):
        self.mod_name = mod_name
        self.case_name = case_name
        # exec-phase
        self.result = None  # SUCCESS, FAIL, ERROR
        self.io_out: Optional[str] = None              # never set if SUCESS
        self.failure: Optional[FailureInfo] = None     # set if FAIL
        self.error: Optional[ErrorInfo] = None  # set if ERROR



class TestCase:
    def __init__(self, func, cls=None):
        self.cls = cls
        self.func = func

    @property
    def lineno(self) -> int:
        """order tests by line number

        should be used only for tests within same module
        """
        return self.func.__code__.co_firstlineno
