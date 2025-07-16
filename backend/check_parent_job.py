#!/usr/bin/env python
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import Job

async def check_parent_job():
    async with AsyncSessionLocal() as db:
        # Check the parent job
        result = await db.execute(
            select(Job).where(Job.id == "7cf06c90-3888-40b7-9a2e-3d2cc2287b28")
        )
        
        parent_job = result.scalar_one_or_none()
        if parent_job:
            print(f"Parent Job ID: {parent_job.id}")
            print(f"Name: {parent_job.name}")
            print(f"Status: {parent_job.status}")
            print(f"Created: {parent_job.created_at}")
            print(f"Completed: {parent_job.completed_at}")
        else:
            print("Parent job not found")

if __name__ == "__main__":
    asyncio.run(check_parent_job())