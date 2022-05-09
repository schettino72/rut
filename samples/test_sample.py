from rut import check

def func(x):
    return x + 1

def test_ok():
    assert 7 == 6 + 1

class TestX:
    def test_fail(self):
        check(func(1)) == 4

def test_fail():
    check(func(3)) == 5

def calc(n):
    foo = n - 5
    bar = 20 / foo
    return bar

def test_error():
    md = {'my': 'dict'}
    check(calc(5)) == 5.5
