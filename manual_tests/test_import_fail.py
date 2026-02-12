"""Manual test to verify import failure error messages.

Run from project root:
    rut manual_tests/test_import_fail.py

Expected: clean error message about missing module, not raw unittest traceback.
"""
import nonexistent_module_xyz
import unittest


class TestImportFail(unittest.TestCase):
    def test_something(self):
        self.assertTrue(True)
