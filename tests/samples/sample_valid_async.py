import unittest

class ValidAsyncTest(unittest.IsolatedAsyncioTestCase):
    async def test_a_valid_async_test(self):
        self.assertTrue(True)
