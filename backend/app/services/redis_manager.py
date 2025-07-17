import json
from typing import Optional, List
from redis import asyncio as aioredis

from app.core.config import settings


class RedisManager:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.job_queue_key = "ctf_rclone:job_queue"
        self.job_status_prefix = "ctf_rclone:job_status:"
        self.endpoint_counters_prefix = "ctf_rclone:endpoint_counters:"
        
    async def connect(self):
        """Initialize Redis connection"""
        self.redis = await aioredis.from_url(
            str(settings.REDIS_URL),
            encoding="utf-8",
            decode_responses=True
        )
        
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            
    async def enqueue_job(self, job_id: str, priority: int = 0, delay: int = 0) -> int:
        """Add job to the queue with priority (lower number = higher priority)
        
        Args:
            job_id: The job ID to enqueue
            priority: Priority score (lower = higher priority)
            delay: Delay in seconds before job is available for processing
        """
        import time
        score = priority
        if delay > 0:
            # Use timestamp as score for delayed jobs
            score = time.time() + delay
        return await self.redis.zadd(self.job_queue_key, {job_id: score})
    
    async def dequeue_job(self) -> Optional[str]:
        """Get the highest priority job from the queue
        
        Only returns jobs that are ready to run (score <= current time)
        """
        import time
        current_time = time.time()
        
        # Get jobs with score less than current time
        result = await self.redis.zrangebyscore(
            self.job_queue_key, 
            '-inf', 
            current_time, 
            start=0, 
            num=1,
            withscores=True
        )
        
        if result:
            job_id = result[0][0]
            # Remove the job from queue
            await self.redis.zrem(self.job_queue_key, job_id)
            return job_id
        return None
    
    async def get_queue_length(self) -> int:
        """Get the number of jobs in the queue"""
        return await self.redis.zcard(self.job_queue_key)
    
    async def set_job_status(self, job_id: str, status: dict) -> None:
        """Store job status in Redis with TTL"""
        key = f"{self.job_status_prefix}{job_id}"
        await self.redis.setex(
            key,
            86400,  # 24 hour TTL
            json.dumps(status)
        )
    
    async def get_job_status(self, job_id: str) -> Optional[dict]:
        """Get job status from Redis"""
        key = f"{self.job_status_prefix}{job_id}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def increment_endpoint_counter(self, endpoint_id: str) -> int:
        """Increment active transfer counter for an endpoint"""
        key = f"{self.endpoint_counters_prefix}{endpoint_id}"
        return await self.redis.incr(key)
    
    async def decrement_endpoint_counter(self, endpoint_id: str) -> int:
        """Decrement active transfer counter for an endpoint"""
        key = f"{self.endpoint_counters_prefix}{endpoint_id}"
        value = await self.redis.decr(key)
        # Ensure counter doesn't go negative
        if value < 0:
            await self.redis.set(key, 0)
            return 0
        return value
    
    async def get_endpoint_counter(self, endpoint_id: str) -> int:
        """Get current active transfer count for an endpoint"""
        key = f"{self.endpoint_counters_prefix}{endpoint_id}"
        value = await self.redis.get(key)
        return int(value) if value else 0
    
    async def reset_endpoint_counter(self, endpoint_id: str) -> None:
        """Reset endpoint counter to 0"""
        key = f"{self.endpoint_counters_prefix}{endpoint_id}"
        await self.redis.set(key, 0)
    
    async def publish_event(self, channel: str, message: dict) -> None:
        """Publish event to Redis pub/sub channel"""
        await self.redis.publish(channel, json.dumps(message))
    
    async def subscribe(self, channels: List[str]):
        """Subscribe to Redis channels"""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub


# Global instance
redis_manager = RedisManager()