"""Imports test_zebra. Should run after test_zebra in topological order."""
import unittest
from tests.samples.topo import test_zebra  # noqa: F401


class TestMiddle(unittest.TestCase):
    def test_middle(self):
        pass
