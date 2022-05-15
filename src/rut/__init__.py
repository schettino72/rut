from .checker import check

__all__ = ['check']


def fixture(func):
    return func

class Fixture:
    def __init__(self, func, args, kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

def use(*args, **kwargs):
    """
       args:
         - if first parameter is a string, it corresponds to the param name
         - fixture function. if name was ommited, get name from function
         - remaining positional args are to be passed to fixture function
    """
    def deco(func):
        if not hasattr(func, 'use_fix'):
            func.use_fix = {}
        if isinstance(args[0], str):
            name, fix, *fix_args = args
        else:
            fix, *fix_args = args
            name = fix.__name__
        func.use_fix[name] = Fixture(fix, fix_args, kwargs)
        return func
    return deco
