from contextlib import contextmanager


class TestFailure(Exception):
    """test assertion/check failure

    - args[0] str with Exception basic description
    - args[1] value being checked
    """

    @property
    def val(self):
        return self.args[1]

    # never used?
    # def __str__(self):
    #     return f'TestFailure {self.args[0]} for value {self.val!r}.'


class CheckComparisonFailure(TestFailure):
    """Check value against other
    """
    @property
    def other(self):
        return self.args[2]


class CheckEqualityFailure(CheckComparisonFailure):
    """error on ==
    Usage: CheckEqualityFailure('Not Equal', 1, 2)
    """
    def __str__(self):
        return (f'TestFailure - {self.args[0]}. '
                f'Got => {self.val!r}, expected => {self.other!r}.')




class ExpectedException:
    def __init__(self, expected_cls):
        self.expected = expected_cls
        self.raised = None


class check:
    def __init__(self, val):
        self.val = val
        self._used = False

    def __eq__(self, other):
        self._used = True
        if self.val != other:
            raise CheckEqualityFailure("Not equal", self.val, other)

    @contextmanager
    @staticmethod
    def raises(expected_cls):
        exc_info = ExpectedException(expected_cls)
        try:
            yield exc_info
        except expected_cls as exp:
            exc_info.raised = exp
        except Exception as exp:
            raise TestFailure('Not the expected exception kind', expected_cls, exp)
        else:
            raise TestFailure('No exception raised', expected_cls)

