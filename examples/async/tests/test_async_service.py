"""Tests for the async service module."""

import unittest
from async_service import AsyncService


class TestAsyncService(unittest.IsolatedAsyncioTestCase):
    """Test cases for the AsyncService class.
    
    Note: We inherit from IsolatedAsyncioTestCase to enable async tests.
    """
    
    async def asyncSetUp(self):
        """Set up async test fixtures.
        
        This is the async version of setUp().
        """
        self.service = AsyncService()
    
    async def test_fetch_data(self):
        """Test fetching a single item."""
        result = await self.service.fetch_data(1)
        
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["name"], "Item 1")
        self.assertIsInstance(result, dict)
    
    async def test_process_data(self):
        """Test data processing."""
        input_data = {"id": 1, "name": "Test"}
        result = await self.service.process_data(input_data)
        
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["name"], "Test")
        self.assertTrue(result["processed"])
    
    async def test_fetch_and_process(self):
        """Test the combined fetch and process operation."""
        result = await self.service.fetch_and_process(2)
        
        self.assertEqual(result["id"], 2)
        self.assertEqual(result["name"], "Item 2")
        self.assertTrue(result["processed"])
    
    async def test_concurrent_operations(self):
        """Test fetching multiple items concurrently."""
        item_ids = [1, 2, 3, 4, 5]
        results = await self.service.fetch_multiple(item_ids)
        
        self.assertEqual(len(results), 5)
        for i, result in enumerate(results):
            self.assertEqual(result["id"], i + 1)
            self.assertEqual(result["name"], f"Item {i + 1}")
    
    async def test_error_handling(self):
        """Test that errors in async code are properly caught."""
        # This test demonstrates that exceptions work normally
        with self.assertRaises(TypeError):
            await self.service.fetch_data("invalid")  # Should be int
