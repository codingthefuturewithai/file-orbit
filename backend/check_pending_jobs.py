#!/usr/bin/env python
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import Job
from app.models.job import JobStatus, JobType

async def check_pending_jobs():
    async with AsyncSessionLocal() as db:
        # Check pending chain jobs
        result = await db.execute(
            select(Job).where(
                Job.type == JobType.CHAINED,
                Job.status == JobStatus.PENDING
            )
        )
        
        pending_jobs = result.scalars().all()
        print(f"Found {len(pending_jobs)} PENDING chain jobs:")
        
        for job in pending_jobs[:5]:  # Show first 5
            print(f"\nJob ID: {job.id}")
            print(f"Name: {job.name}")
            print(f"Source Path: {job.source_path}")
            print(f"Parent Job ID: {job.parent_job_id}")
            print(f"Created: {job.created_at}")
        
        # Check queued chain jobs
        result = await db.execute(
            select(Job).where(
                Job.type == JobType.CHAINED,
                Job.status == JobStatus.QUEUED
            )
        )
        
        queued_jobs = result.scalars().all()
        print(f"\n\nFound {len(queued_jobs)} QUEUED chain jobs")

if __name__ == "__main__":
    asyncio.run(check_pending_jobs())