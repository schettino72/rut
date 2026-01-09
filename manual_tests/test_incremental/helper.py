"""Middle dependency - imports util."""

from manual_tests.test_incremental import util


def double_value():
    return util.get_value() * 2
