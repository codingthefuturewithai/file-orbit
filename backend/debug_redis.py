#!/usr/bin/env python3
"""Debug script to check Redis queue status"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.services.redis_manager import redis_manager
from app.core.config import settings

async def main():
    """Check Redis queue status"""
    try:
        # Connect to Redis
        await redis_manager.connect()
        print(f"Connected to Redis at {settings.REDIS_URL}")
        
        # Check queue length
        queue_length = await redis_manager.get_queue_length()
        print(f"\nJob queue length: {queue_length}")
        
        # Check if we can access Redis at all
        if redis_manager.redis:
            # Try to get all jobs in queue
            jobs = await redis_manager.redis.zrange(redis_manager.job_queue_key, 0, -1, withscores=True)
            print(f"\nJobs in queue:")
            for job_id, score in jobs:
                print(f"  - Job ID: {job_id}, Score: {score}")
                
                # Check job status
                status = await redis_manager.get_job_status(job_id)
                if status:
                    print(f"    Status: {status}")
        else:
            print("Redis connection not established")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await redis_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())