#!/usr/bin/env python3
"""
Test script for creating and managing scheduled jobs
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.core.database import get_db, engine
from app.models.job import Job, JobType, JobStatus
from app.models.endpoint import Endpoint
from app.services.scheduler import JobScheduler
from app.services.redis_manager import redis_manager
from sqlalchemy import select
import uuid


async def create_test_endpoints():
    """Create test endpoints if they don't exist"""
    async for db in get_db():
        try:
            # Check for existing test endpoints
            result = await db.execute(
                select(Endpoint).where(Endpoint.name.in_(["Test Source", "Test Destination"]))
            )
            endpoints = result.scalars().all()
            
            if len(endpoints) < 2:
                # Create test source endpoint
                source = Endpoint(
                    id=str(uuid.uuid4()),
                    name="Test Source",
                    type="local",
                    config={
                        "path": "/tmp/test_source"
                    },
                    is_active=True,
                    created_at=datetime.now(timezone.utc)
                )
                
                # Create test destination endpoint
                destination = Endpoint(
                    id=str(uuid.uuid4()),
                    name="Test Destination",
                    type="local",
                    config={
                        "path": "/tmp/test_destination"
                    },
                    is_active=True,
                    created_at=datetime.now(timezone.utc)
                )
                
                db.add(source)
                db.add(destination)
                await db.commit()
                
                return source.id, destination.id
            else:
                # Return existing endpoint IDs
                source_id = next(e.id for e in endpoints if "Source" in e.name)
                dest_id = next(e.id for e in endpoints if "Destination" in e.name)
                return source_id, dest_id
                
        finally:
            await db.close()


async def create_scheduled_jobs():
    """Create test scheduled jobs"""
    source_id, dest_id = await create_test_endpoints()
    
    async for db in get_db():
        try:
            # Create scheduler instance to validate cron expressions
            scheduler = JobScheduler(redis_manager)
            
            # Define test scheduled jobs
            test_jobs = [
                {
                    "name": "Hourly Backup",
                    "schedule": "0 * * * *",  # Every hour at minute 0
                    "description": "Backup files every hour",
                    "source_path": "/data/important",
                    "destination_path": "/backup/hourly/{year}-{month}-{day}/{hour}",
                    "file_pattern": "*.dat"
                },
                {
                    "name": "Daily Report Transfer",
                    "schedule": "30 8 * * *",  # Every day at 8:30 AM
                    "description": "Transfer daily reports",
                    "source_path": "/reports/daily",
                    "destination_path": "/archive/reports/{year}/{month}/{day}",
                    "file_pattern": "*.pdf"
                },
                {
                    "name": "Every 5 Minutes Test",
                    "schedule": "*/5 * * * *",  # Every 5 minutes
                    "description": "Test job that runs frequently",
                    "source_path": "/test/input",
                    "destination_path": "/test/output/{timestamp}",
                    "file_pattern": "*"
                },
                {
                    "name": "Weekly Archive",
                    "schedule": "0 2 * * 0",  # Every Sunday at 2:00 AM
                    "description": "Weekly archive of completed work",
                    "source_path": "/work/completed",
                    "destination_path": "/archive/weekly/{year}/week-{timestamp}",
                    "file_pattern": "*",
                    "delete_source": True
                }
            ]
            
            created_jobs = []
            
            for job_data in test_jobs:
                # Validate cron expression
                if not scheduler.validate_cron_expression(job_data["schedule"]):
                    print(f"Invalid cron expression for {job_data['name']}: {job_data['schedule']}")
                    continue
                
                # Calculate next run time
                next_run = scheduler._calculate_next_run(job_data["schedule"])
                
                # Create scheduled job
                job = Job(
                    id=str(uuid.uuid4()),
                    name=job_data["name"],
                    description=job_data.get("description"),
                    type=JobType.SCHEDULED,
                    schedule=job_data["schedule"],
                    source_endpoint_id=source_id,
                    source_path=job_data["source_path"],
                    destination_endpoint_id=dest_id,
                    destination_path=job_data["destination_path"],
                    file_pattern=job_data["file_pattern"],
                    delete_source_after_transfer=job_data.get("delete_source", False),
                    status=JobStatus.SCHEDULED,
                    is_active=True,
                    next_run_at=next_run,
                    total_runs=0,
                    config={
                        "test_job": True
                    },
                    created_at=datetime.now(timezone.utc),
                    created_by="test_script"
                )
                
                db.add(job)
                created_jobs.append(job)
                
            await db.commit()
            
            print(f"\nCreated {len(created_jobs)} scheduled jobs:")
            for job in created_jobs:
                print(f"\n- {job.name}")
                print(f"  Schedule: {job.schedule}")
                print(f"  Next run: {job.next_run_at}")
                print(f"  Source: {job.source_path}")
                print(f"  Destination: {job.destination_path}")
                
                # Show next 5 run times
                next_runs = scheduler.get_next_runs(job.schedule, 5)
                if next_runs:
                    print("  Upcoming runs:")
                    for i, run_time in enumerate(next_runs, 1):
                        print(f"    {i}. {run_time}")
                        
        except Exception as e:
            print(f"Error creating scheduled jobs: {e}")
            await db.rollback()
        finally:
            await db.close()


async def list_scheduled_jobs():
    """List all scheduled jobs"""
    async for db in get_db():
        try:
            result = await db.execute(
                select(Job).where(
                    Job.type == JobType.SCHEDULED,
                    Job.is_active == True
                ).order_by(Job.next_run_at)
            )
            jobs = result.scalars().all()
            
            print(f"\n\nActive Scheduled Jobs ({len(jobs)} total):")
            print("-" * 80)
            
            for job in jobs:
                print(f"\nJob: {job.name} (ID: {job.id})")
                print(f"  Schedule: {job.schedule}")
                print(f"  Status: {job.status}")
                print(f"  Next run: {job.next_run_at}")
                print(f"  Last run: {job.last_run_at}")
                print(f"  Total runs: {job.total_runs}")
                print(f"  Source: {job.source_path}")
                print(f"  Destination: {job.destination_path}")
                
        finally:
            await db.close()


async def test_scheduler_execution():
    """Test the scheduler by running it briefly"""
    print("\n\nTesting scheduler execution...")
    print("Starting scheduler for 30 seconds...")
    
    scheduler = JobScheduler(redis_manager)
    
    # Start scheduler
    await scheduler.start()
    
    # Run for 30 seconds
    await asyncio.sleep(30)
    
    # Stop scheduler
    await scheduler.stop()
    
    print("Scheduler test completed")


async def check_job_executions():
    """Check for jobs created by the scheduler"""
    async for db in get_db():
        try:
            # Look for manual jobs created by scheduler
            result = await db.execute(
                select(Job).where(
                    Job.type == JobType.MANUAL,
                    Job.config.op('->>')('scheduled_execution') == 'true'
                ).order_by(Job.created_at.desc()).limit(10)
            )
            executions = result.scalars().all()
            
            if executions:
                print(f"\n\nRecent Scheduled Job Executions ({len(executions)} found):")
                print("-" * 80)
                
                for job in executions:
                    scheduled_job_id = job.config.get('scheduled_job_id')
                    print(f"\nExecution: {job.name}")
                    print(f"  Job ID: {job.id}")
                    print(f"  Scheduled Job ID: {scheduled_job_id}")
                    print(f"  Status: {job.status}")
                    print(f"  Created: {job.created_at}")
                    print(f"  Started: {job.started_at}")
                    print(f"  Completed: {job.completed_at}")
            else:
                print("\nNo scheduled job executions found yet")
                
        finally:
            await db.close()


async def main():
    """Main test function"""
    print("PBS Rclone POC - Scheduled Jobs Test")
    print("=" * 80)
    
    # Create test scheduled jobs
    await create_scheduled_jobs()
    
    # List all scheduled jobs
    await list_scheduled_jobs()
    
    # Optionally test scheduler execution
    print("\n\nWould you like to test the scheduler? (y/n): ", end="")
    response = input().strip().lower()
    
    if response == 'y':
        await test_scheduler_execution()
        
        # Check for executed jobs
        await check_job_executions()
    
    print("\n\nScheduled jobs test completed!")
    print("\nTo run the scheduler service continuously, use:")
    print("  python scheduler_service.py")


if __name__ == "__main__":
    asyncio.run(main())