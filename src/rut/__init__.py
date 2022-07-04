from .checker import check
from .case import skip_test

__all__ = ['check', 'skip_test']


def fixture(original_func=None, *, params=None):
    def _decorate(func):
        func.rut_scope = 'function'
        func.params = params  # params of fixture itself
        return func
    if original_func:  # decorator without arguments @fixture
        return _decorate(original_func)
    else:  # decorator with arguments @fixture(params=['foo', 'bar'])
        return _decorate


class Fixture:
    """reference to a fixture"""
    def __init__(self, func, args, kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.params = func.params  # parametrization values

def use(*args, **kwargs):
    """
       args:
         - if first parameter is a string, it corresponds to the param name
         - fixture function. if name was ommited, get name from function
         - remaining positional args are to be passed to fixture function
    """
    # TODO:
    # 1) make sure func has a fixture decorator
    # 2) support params
    # 3) support return instead of yield
    # 4) scope - function, class, module, session
    def deco(func):
        # add dict containing fixture instances
        if not hasattr(func, 'use_fix'):
            func.use_fix = {}

        # handle use() having an explicit parameter name passed as first parameter
        if isinstance(args[0], str):
            name, fix, *fix_args = args
        else:
            fix, *fix_args = args
            name = fix.__name__
        func.use_fix[name] = Fixture(fix, fix_args, kwargs)
        return func
    return deco
