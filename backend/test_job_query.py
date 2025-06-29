#!/usr/bin/env python3
"""Test job query to debug SQLAlchemy issue"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.models.job import Job
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def main():
    """Test job query"""
    async with AsyncSessionLocal() as db:
        try:
            # Print the columns SQLAlchemy thinks the Job model has
            print("Job model columns:")
            for column in Job.__table__.columns:
                print(f"  - {column.name}: {column.type}")
            
            print("\n" + "="*50 + "\n")
            
            # Try to execute a simple query
            print("Executing query...")
            result = await db.execute(
                select(Job)
                .options(
                    selectinload(Job.source_endpoint),
                    selectinload(Job.destination_endpoint)
                )
                .limit(1)
            )
            
            job = result.scalar_one_or_none()
            if job:
                print(f"Found job: {job.id}")
            else:
                print("No jobs found")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())