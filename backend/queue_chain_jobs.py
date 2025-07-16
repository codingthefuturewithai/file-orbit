#!/usr/bin/env python
import asyncio
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models import Job
from app.models.job import JobStatus, JobType

async def queue_chain_jobs():
    async with AsyncSessionLocal() as db:
        # Find all PENDING chain jobs with completed parent jobs
        result = await db.execute(
            select(Job).where(
                Job.type == JobType.CHAINED,
                Job.status == JobStatus.PENDING
            )
        )
        
        pending_chain_jobs = result.scalars().all()
        print(f"Found {len(pending_chain_jobs)} PENDING chain jobs")
        
        queued_count = 0
        for job in pending_chain_jobs:
            # Check if parent job is completed
            parent_result = await db.execute(
                select(Job).where(Job.id == job.parent_job_id)
            )
            parent_job = parent_result.scalar_one_or_none()
            
            if parent_job and parent_job.status == JobStatus.COMPLETED:
                # Queue this chain job
                await db.execute(
                    update(Job).where(Job.id == job.id).values(
                        status=JobStatus.QUEUED
                    )
                )
                queued_count += 1
                print(f"Queued chain job: {job.id} ({job.name})")
        
        await db.commit()
        print(f"\nQueued {queued_count} chain jobs")

if __name__ == "__main__":
    asyncio.run(queue_chain_jobs())