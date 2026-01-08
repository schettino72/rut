"""Imports test_middle. Should run last in topological order."""
import unittest
from tests.samples.topo import test_middle  # noqa: F401


class TestApple(unittest.TestCase):
    def test_apple(self):
        pass
