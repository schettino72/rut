from rut import check

from rut import checker


class TestCheckerIs:
    def test_is(self):
        check(True).is_(True)

    def test_eq_fail(self):
        with check.raises(checker.CheckFailure):
            check(2).is_(True)

class TestCheckerEq:
    def test_eq_ok(self):
        check(3) == 3

    def test_eq_fail(self):
        with check.raises(checker.CheckFailure) as exc_info:
            check(1) == 2
        check(exc_info.raised.args[1:]) == (1, 2)
        check(str(exc_info.raised)) == 'CheckFailure - Not equal. Got => 1, expected => 2.'


class TestContains:
    def test_contains_true(self):
        check([1, 2, 3]).contains(1)

    def test_contains_false(self):
        with check.raises(checker.CheckContainsFailure):
            check([1, 2, 3]).contains(5)

    def test_not_contains_true(self):
        check([1, 2, 3]).not_contains(5)

    def test_not_contains_false(self):
        with check.raises(checker.CheckContainsFailure):
            check([1, 2, 3]).not_contains(1)

    def test_in_not_implemented(self):
        with check.raises(NotImplementedError):
            1 in check([1, 2, 3])


class TestCheckerRaise:
    def test_raises_pass(self):
        class CustomException(Exception):
            pass
        with check.raises(CustomException) as exc_info:
            raise CustomException('has error')
        check(str(exc_info.raised)) == 'has error'

    def test_raises_wrong_exception(self):
        class CustomException(Exception):
            pass
        try:
            with check.raises(ValueError):
                raise CustomException('has error')
        except checker.CheckFailure as failure:
            check(failure.args[0]) == 'Not the expected exception kind'
        else:  # pragma: no cover
            assert False

    def test_raises_nothing(self):
        class CustomException(Exception):
            pass
        try:
            with check.raises(ValueError):
                pass
        except checker.CheckFailure as failure:
            check(failure.args[0]) == 'No exception raised'
        else:  # pragma: no cover
            assert False


class TestCheckerStartswith:
    def test_ok(self):
        check('They say jump').startswith('They say')

    def test_fail(self):
        with check.raises(checker.CheckFailure):
            check('You say jump').startswith('They say')


class TestChecker_HasLine:
    def test_ok(self):
        check('They say\nYou say\n').has_line('You say')

    def test_fail(self):
        with check.raises(checker.CheckFailure):
            check('They say\nYou say\n').has_line('They')

