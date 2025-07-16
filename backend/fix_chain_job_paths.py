#!/usr/bin/env python
import asyncio
import os
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models import Job
from app.models.job import JobStatus, JobType

async def fix_chain_job_paths():
    async with AsyncSessionLocal() as db:
        # Find all chain jobs with file patterns
        result = await db.execute(
            select(Job).where(
                Job.type == JobType.CHAINED,
                Job.file_pattern == '*'
            )
        )
        
        chain_jobs = result.scalars().all()
        print(f"Found {len(chain_jobs)} chain jobs to fix")
        
        fixed_count = 0
        for job in chain_jobs:
            # Check if source_path contains a filename
            if job.source_path and '.' in os.path.basename(job.source_path):
                # Extract directory and filename
                dir_path = os.path.dirname(job.source_path)
                file_name = os.path.basename(job.source_path)
                
                print(f"\nFixing job {job.id}:")
                print(f"  Old: source_path='{job.source_path}', file_pattern='{job.file_pattern}'")
                print(f"  New: source_path='{dir_path}', file_pattern='{file_name}'")
                
                # Update the job
                await db.execute(
                    update(Job).where(Job.id == job.id).values(
                        source_path=dir_path,
                        file_pattern=file_name
                    )
                )
                fixed_count += 1
        
        await db.commit()
        print(f"\nFixed {fixed_count} chain jobs")

if __name__ == "__main__":
    asyncio.run(fix_chain_job_paths())