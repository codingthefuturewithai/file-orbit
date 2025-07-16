from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus, JobType
from app.schemas.job import JobCreate

import logging
logger = logging.getLogger(__name__)


class ChainJobService:
    """Service for creating and managing chain jobs from transfer templates"""
    
    @staticmethod
    async def create_chain_jobs(
        parent_job: Job,
        chain_rules: List[Dict[str, str]],
        db: AsyncSession
    ) -> List[Job]:
        """
        Create chain jobs from chain rules
        
        Args:
            parent_job: The parent job that chain jobs will depend on
            chain_rules: List of chain rule definitions with endpoint_id and path_template
            db: Database session
            
        Returns:
            List of created chain jobs
        """
        if not chain_rules:
            return []
            
        created_jobs = []
        
        for idx, chain_rule in enumerate(chain_rules):
            try:
                # Create job data for chain job
                chain_job_data = JobCreate(
                    name=f"{parent_job.name} - Chain {idx + 1}",
                    type=JobType.CHAINED,
                    source_endpoint_id=parent_job.destination_endpoint_id,  # Previous destination becomes source
                    source_path=parent_job.destination_path,
                    destination_endpoint_id=chain_rule['endpoint_id'],
                    destination_path=ChainJobService._apply_path_template(
                        chain_rule['path_template'],
                        parent_job.destination_path
                    ),
                    file_pattern=parent_job.file_pattern,
                    delete_source_after_transfer=False,  # Don't delete intermediate files
                    is_active=True,
                    config={
                        'parent_job_id': parent_job.id,
                        'chain_index': idx,
                        'chain_rule': chain_rule
                    }
                )
                
                # Create the job
                chain_job = Job(
                    id=str(uuid.uuid4()),
                    **chain_job_data.model_dump(),
                    parent_job_id=parent_job.id,
                    status=JobStatus.PENDING,  # Will be queued after parent completes
                    created_at=datetime.now(timezone.utc)
                )
                
                db.add(chain_job)
                created_jobs.append(chain_job)
                
                logger.info(f"Created chain job {chain_job.id} for parent job {parent_job.id}")
                
            except Exception as e:
                logger.error(f"Error creating chain job {idx} for parent job {parent_job.id}: {e}")
                # Continue creating other chain jobs even if one fails
                continue
        
        if created_jobs:
            await db.commit()
            
        return created_jobs
    
    @staticmethod
    def _apply_path_template(template: str, source_path: str) -> str:
        """
        Apply variables to destination path template
        
        Supports variables:
        - {year}: Current year
        - {month}: Current month (zero-padded)
        - {day}: Current day (zero-padded)
        - {filename}: Full filename from source path
        - {basename}: Filename without extension
        - {extension}: File extension
        """
        import os
        from datetime import datetime
        
        # Extract filename components
        filename = os.path.basename(source_path)
        basename, extension = os.path.splitext(filename)
        
        # Get current date components
        now = datetime.now()
        
        # Apply substitutions
        result = template
        result = result.replace('{year}', str(now.year))
        result = result.replace('{month}', f'{now.month:02d}')
        result = result.replace('{day}', f'{now.day:02d}')
        result = result.replace('{filename}', filename)
        result = result.replace('{basename}', basename)
        result = result.replace('{extension}', extension.lstrip('.'))
        
        return result
    
    @staticmethod
    async def get_chain_jobs(parent_job_id: str, db: AsyncSession) -> List[Job]:
        """
        Get all chain jobs for a parent job
        
        Args:
            parent_job_id: ID of the parent job
            db: Database session
            
        Returns:
            List of chain jobs
        """
        from sqlalchemy import select
        
        result = await db.execute(
            select(Job).where(Job.parent_job_id == parent_job_id)
        )
        return result.scalars().all()