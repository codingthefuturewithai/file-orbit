"""
Job scheduler service for executing scheduled transfers
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from croniter import croniter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db
from app.models.job import Job, JobType, JobStatus
from app.services.redis_manager import RedisManager

logger = logging.getLogger(__name__)


class JobScheduler:
    """Manages scheduled job execution"""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager
        self.running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._check_interval = 60  # Check every minute
        
    async def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        self.running = True
        logger.info("Starting job scheduler")
        
        # Update next run times for all scheduled jobs
        await self._update_all_next_run_times()
        
        # Start scheduler loop
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        
    async def stop(self):
        """Stop the scheduler"""
        logger.info("Stopping job scheduler")
        self.running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
                
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                await self._check_scheduled_jobs()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                
            # Wait before next check
            await asyncio.sleep(self._check_interval)
            
    async def _check_scheduled_jobs(self):
        """Check for jobs that need to be executed"""
        async for db in get_db():
            try:
                # Find jobs that are due to run
                now = datetime.now(timezone.utc)
                
                result = await db.execute(
                    select(Job).where(
                        Job.type == JobType.SCHEDULED,
                        Job.is_active == True,
                        Job.next_run_at <= now
                    )
                )
                jobs = result.scalars().all()
                
                for job in jobs:
                    await self._execute_scheduled_job(job, db)
                    
            except Exception as e:
                logger.error(f"Error checking scheduled jobs: {e}")
            finally:
                await db.close()
                
    async def _execute_scheduled_job(self, job: Job, db: AsyncSession):
        """Execute a scheduled job"""
        try:
            logger.info(f"Executing scheduled job: {job.name} (ID: {job.id})")
            
            # Update job statistics
            job.last_run_at = datetime.now(timezone.utc)
            job.total_runs += 1
            
            # Calculate next run time
            next_run = self._calculate_next_run(job.schedule)
            job.next_run_at = next_run
            
            # Create a copy of the job for execution
            # This allows the scheduled job to remain for future runs
            import uuid
            execution_job = Job(
                id=str(uuid.uuid4()),
                name=f"{job.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                type=JobType.MANUAL,  # Execute as manual job
                source_endpoint_id=job.source_endpoint_id,
                source_path=job.source_path,
                destination_endpoint_id=job.destination_endpoint_id,
                destination_path=job.destination_path,
                file_pattern=job.file_pattern,
                delete_source_after_transfer=job.delete_source_after_transfer,
                status=JobStatus.QUEUED,
                is_active=True,
                config={
                    'scheduled_job_id': job.id,
                    'scheduled_execution': True
                },
                created_at=datetime.now(timezone.utc),
                created_by=job.created_by
            )
            
            db.add(execution_job)
            await db.commit()
            
            # Queue the job for processing
            await self.redis_manager.queue_job(execution_job.id)
            
            logger.info(f"Queued execution job {execution_job.id} for scheduled job {job.id}")
            
        except Exception as e:
            logger.error(f"Error executing scheduled job {job.id}: {e}")
            await db.rollback()
            
    def _calculate_next_run(self, schedule: Optional[str]) -> Optional[datetime]:
        """Calculate the next run time based on cron schedule"""
        if not schedule:
            return None
            
        try:
            # Parse cron expression
            base_time = datetime.now(timezone.utc)
            cron = croniter(schedule, base_time)
            next_time = cron.get_next(datetime)
            
            # Ensure it's timezone-aware
            if next_time.tzinfo is None:
                next_time = next_time.replace(tzinfo=timezone.utc)
                
            return next_time
            
        except Exception as e:
            logger.error(f"Error parsing cron schedule '{schedule}': {e}")
            return None
            
    async def _update_all_next_run_times(self):
        """Update next run times for all scheduled jobs"""
        async for db in get_db():
            try:
                result = await db.execute(
                    select(Job).where(
                        Job.type == JobType.SCHEDULED,
                        Job.is_active == True
                    )
                )
                jobs = result.scalars().all()
                
                for job in jobs:
                    if job.schedule:
                        next_run = self._calculate_next_run(job.schedule)
                        if next_run:
                            job.next_run_at = next_run
                            
                await db.commit()
                logger.info(f"Updated next run times for {len(jobs)} scheduled jobs")
                
            except Exception as e:
                logger.error(f"Error updating next run times: {e}")
                await db.rollback()
            finally:
                await db.close()
                
    def validate_cron_expression(self, expression: str) -> bool:
        """Validate a cron expression"""
        try:
            croniter(expression)
            return True
        except Exception:
            return False
            
    def get_next_runs(self, schedule: str, count: int = 5) -> List[datetime]:
        """Get the next N run times for a schedule"""
        try:
            base_time = datetime.now(timezone.utc)
            cron = croniter(schedule, base_time)
            
            runs = []
            for _ in range(count):
                next_time = cron.get_next(datetime)
                if next_time.tzinfo is None:
                    next_time = next_time.replace(tzinfo=timezone.utc)
                runs.append(next_time)
                
            return runs
            
        except Exception as e:
            logger.error(f"Error getting next runs for schedule '{schedule}': {e}")
            return []