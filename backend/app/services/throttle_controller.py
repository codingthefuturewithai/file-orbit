import asyncio
from typing import Dict
import logging
from datetime import datetime

from app.services.redis_manager import redis_manager
from app.core.database import AsyncSessionLocal
from app.models.endpoint import Endpoint
from sqlalchemy import select

logger = logging.getLogger(__name__)


class ThrottleController:
    """
    Controls concurrent transfer limits per endpoint.
    Uses Redis for distributed counting across multiple workers.
    """
    
    def __init__(self):
        self.endpoint_limits: Dict[str, int] = {}
        self.lock_timeout = 30  # seconds
        
    async def load_endpoint_limits(self):
        """Load endpoint throttle limits from database"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Endpoint))
            endpoints = result.scalars().all()
            
            for endpoint in endpoints:
                self.endpoint_limits[endpoint.id] = endpoint.max_concurrent_transfers
                
        logger.info(f"Loaded throttle limits for {len(self.endpoint_limits)} endpoints")
    
    async def acquire_slot(self, endpoint_id: str, timeout: int = 30) -> bool:
        """
        Try to acquire a transfer slot for an endpoint.
        
        Args:
            endpoint_id: The endpoint to acquire a slot for
            timeout: Maximum time to wait for a slot (seconds)
            
        Returns:
            True if slot acquired, False if timeout
        """
        # Get limit for endpoint
        limit = self.endpoint_limits.get(endpoint_id)
        if limit is None:
            # Reload limits if endpoint not found
            await self.load_endpoint_limits()
            limit = self.endpoint_limits.get(endpoint_id, 5)  # Default to 5
        
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            # Get current count
            current = await redis_manager.get_endpoint_counter(endpoint_id)
            
            if current < limit:
                # Try to increment
                new_count = await redis_manager.increment_endpoint_counter(endpoint_id)
                
                # Check if we got the slot (handle race condition)
                if new_count <= limit:
                    logger.info(f"Acquired slot for endpoint {endpoint_id}: {new_count}/{limit}")
                    return True
                else:
                    # Over limit, decrement back
                    await redis_manager.decrement_endpoint_counter(endpoint_id)
            
            # Wait before retry
            await asyncio.sleep(1)
        
        logger.warning(f"Timeout acquiring slot for endpoint {endpoint_id}")
        return False
    
    async def release_slot(self, endpoint_id: str):
        """Release a transfer slot for an endpoint"""
        count = await redis_manager.decrement_endpoint_counter(endpoint_id)
        logger.info(f"Released slot for endpoint {endpoint_id}: {count} remaining")
    
    async def get_endpoint_status(self, endpoint_id: str) -> Dict[str, int]:
        """Get current status for an endpoint"""
        current = await redis_manager.get_endpoint_counter(endpoint_id)
        limit = self.endpoint_limits.get(endpoint_id, 5)
        
        return {
            "current": current,
            "limit": limit,
            "available": max(0, limit - current)
        }
    
    async def get_all_endpoint_status(self) -> Dict[str, Dict[str, int]]:
        """Get status for all endpoints"""
        status = {}
        
        for endpoint_id in self.endpoint_limits:
            status[endpoint_id] = await self.get_endpoint_status(endpoint_id)
        
        return status
    
    async def reset_endpoint_counter(self, endpoint_id: str):
        """Reset counter for an endpoint (admin use)"""
        await redis_manager.reset_endpoint_counter(endpoint_id)
        logger.warning(f"Reset counter for endpoint {endpoint_id}")
    
    async def update_endpoint_limit(self, endpoint_id: str, new_limit: int):
        """Update the limit for an endpoint"""
        self.endpoint_limits[endpoint_id] = new_limit
        logger.info(f"Updated limit for endpoint {endpoint_id} to {new_limit}")
    
    async def check_can_acquire(self, endpoint_id: str) -> bool:
        """Check if a slot can be acquired without actually acquiring it"""
        current = await redis_manager.get_endpoint_counter(endpoint_id)
        limit = self.endpoint_limits.get(endpoint_id, 5)
        return current < limit
    
    async def can_start_transfer(self, source_endpoint_id: str, destination_endpoint_id: str) -> bool:
        """Check if transfer can start for both endpoints"""
        source_can_start = await self.check_can_acquire(source_endpoint_id)
        dest_can_start = await self.check_can_acquire(destination_endpoint_id)
        return source_can_start and dest_can_start


class TransferSlot:
    """Context manager for acquiring/releasing transfer slots"""
    
    def __init__(self, throttle_controller: ThrottleController, endpoint_id: str):
        self.controller = throttle_controller
        self.endpoint_id = endpoint_id
        self.acquired = False
    
    async def __aenter__(self):
        self.acquired = await self.controller.acquire_slot(self.endpoint_id)
        if not self.acquired:
            raise Exception(f"Failed to acquire transfer slot for endpoint {self.endpoint_id}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            await self.controller.release_slot(self.endpoint_id)


# Global instance
throttle_controller = ThrottleController()