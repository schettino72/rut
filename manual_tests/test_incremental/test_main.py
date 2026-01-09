"""Test file - imports helper (which imports util)."""

import unittest

from manual_tests.test_incremental import helper


class TestMain(unittest.TestCase):
    def test_double_value(self):
        self.assertEqual(helper.double_value(), 84)

    def test_helper_uses_util(self):
        self.assertIsNotNone(helper.util.get_value())
