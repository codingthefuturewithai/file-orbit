#!/usr/bin/env python3
"""Test queuing a job"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.services.redis_manager import redis_manager
from app.core.database import AsyncSessionLocal
from app.models.job import Job, JobStatus
from sqlalchemy import select

async def main():
    """Queue a job for testing"""
    try:
        # Connect to Redis
        await redis_manager.connect()
        
        async with AsyncSessionLocal() as db:
            # Get a job to queue
            result = await db.execute(
                select(Job).where(Job.status != JobStatus.RUNNING).limit(1)
            )
            job = result.scalar_one_or_none()
            
            if job:
                print(f"Found job: {job.id} (status: {job.status.value})")
                
                # Queue the job
                await redis_manager.enqueue_job(job.id)
                print(f"Job {job.id} queued successfully")
                
                # Update job status
                job.status = JobStatus.QUEUED
                await db.commit()
                print(f"Job status updated to QUEUED")
                
                # Check queue
                queue_length = await redis_manager.get_queue_length()
                print(f"Current queue length: {queue_length}")
            else:
                print("No jobs available to queue")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await redis_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())