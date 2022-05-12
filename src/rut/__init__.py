from .checker import check

__all__ = ['check']


def fixture(func):
    return func

class Fixture:
    def __init__(self, func, args, kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

def use(name, fix, *args, **kwargs):
    def deco(func):
        if not hasattr(func, 'use_fix'):
            func.use_fix = {}
        func.use_fix[name] = Fixture(fix, args, kwargs)
        return func
    return deco
