from .checker import check

__all__ = ['check']


def fixture(func):
    return func

def use(name, fix):
    def deco(func):
        func.use_fix = {name: fix}
        return func
    return deco
