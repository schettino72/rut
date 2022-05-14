from contextlib import contextmanager


class CheckFailure(Exception):
    """test assertion/check failure

    - args[0] str with Exception basic description
    - args[1] value being checked
    """

    @property
    def val(self):
        return self.args[1]

    # never used?
    # def __str__(self):
    #     return f'CheckFailure {self.args[0]} for value {self.val!r}.'


class CheckComparisonFailure(CheckFailure):
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
        return (f'CheckFailure - {self.args[0]}. '
                f'Got => {self.val!r}, expected => {self.other!r}.')


class CheckContainsFailure(CheckFailure):
    pass

class CheckRaiseFailure(CheckFailure):
    pass



class ExpectedException:
    def __init__(self, expected_cls):
        self.expected = expected_cls
        self.raised = None


class check:
    def __init__(self, val):
        self.val = val

    def __eq__(self, other):
        if self.val != other:
            raise CheckEqualityFailure("Not equal", self.val, other)

    def __contains__(self, other):
        raise NotImplementedError("`in` operator can not be used on check().",
                                  "Use `contains()` / `not_contains()` instead.")

    def contains(self, other):
        if other not in self.val:
            raise CheckContainsFailure("Does not contain", self.val, other)

    def not_contains(self, other):
        if other in self.val:
            raise CheckContainsFailure("Unexpected contains", self.val, other)

    @contextmanager
    @staticmethod
    def raises(expected_cls):
        exc_info = ExpectedException(expected_cls)
        try:
            yield exc_info
        except expected_cls as exp:
            exc_info.raised = exp
        except Exception as exp:
            raise CheckRaiseFailure('Not the expected exception kind', expected_cls, exp)
        else:
            raise CheckRaiseFailure('No exception raised', expected_cls)


    # str methods
    def startswith(self, substr):
        if not self.val.startswith(substr):
            raise CheckFailure('Value does not start with str', self.val, substr)

    def has_line(self, line):
        if line not in self.val.splitlines():
            raise CheckFailure('Line not found', self.val, line)
