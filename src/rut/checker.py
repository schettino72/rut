

class TestFailure(Exception):
    pass

class WrongUsage(TestFailure):
    pass


class check:
    def __init__(self, val):
        self.val = val
        self._used = False


    def __eq__(self, other):
        self._used = True
        if self.val != other:
            raise TestFailure(repr(self.val), '!=', repr(other))


    def __del__(self):
        if not self._used:
            raise WrongUsage('checker NOT USED')
