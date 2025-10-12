"""An async service module for demonstration."""

import asyncio
from typing import List


class AsyncService:
    """A simple async service that simulates network operations."""
    
    async def fetch_data(self, item_id: int) -> dict:
        """Fetch data for an item (simulated with sleep).
        
        Args:
            item_id: The ID of the item to fetch
            
        Returns:
            A dictionary with item data
        """
        # Simulate network delay
        await asyncio.sleep(0.01)
        return {"id": item_id, "name": f"Item {item_id}"}
    
    async def process_data(self, data: dict) -> dict:
        """Process data (simulated with sleep).
        
        Args:
            data: Data to process
            
        Returns:
            Processed data
        """
        # Simulate processing delay
        await asyncio.sleep(0.01)
        return {**data, "processed": True}
    
    async def fetch_and_process(self, item_id: int) -> dict:
        """Fetch and process data for an item.
        
        Args:
            item_id: The ID of the item
            
        Returns:
            Processed item data
        """
        data = await self.fetch_data(item_id)
        return await self.process_data(data)
    
    async def fetch_multiple(self, item_ids: List[int]) -> List[dict]:
        """Fetch multiple items concurrently.
        
        Args:
            item_ids: List of item IDs to fetch
            
        Returns:
            List of item data dictionaries
        """
        tasks = [self.fetch_data(item_id) for item_id in item_ids]
        return await asyncio.gather(*tasks)
