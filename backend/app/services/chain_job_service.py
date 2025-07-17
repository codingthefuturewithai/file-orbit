from typing import List, Dict, Optional
from datetime import datetime, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus, JobType
from app.models.transfer import Transfer
from app.schemas.job import JobCreate

import logging
logger = logging.getLogger(__name__)


class ChainJobService:
    """Service for creating and managing chain jobs from transfer templates"""
    
    @staticmethod
    async def create_chain_jobs(
        parent_job: Job,
        chain_rules: List[Dict[str, str]],
        db: AsyncSession,
        per_file_transfers: Optional[List[Transfer]] = None
    ) -> List[Job]:
        """
        Create chain jobs from chain rules
        
        Args:
            parent_job: The parent job that chain jobs will depend on
            chain_rules: List of chain rule definitions with endpoint_id and path_template
            db: Database session
            per_file_transfers: Optional list of successful transfers for per-file chain creation
            
        Returns:
            List of created chain jobs
        """
        if not chain_rules:
            return []
            
        created_jobs = []
        
        # If per_file_transfers provided, create one chain job per transfer
        if per_file_transfers:
            logger.info(f"Creating per-file chain jobs for {len(per_file_transfers)} transfers")
            return await ChainJobService._create_per_file_chain_jobs(
                parent_job, chain_rules, per_file_transfers, db
            )
        
        # Otherwise, use legacy behavior (one chain job per rule)
        logger.info(f"Creating legacy chain jobs for parent job {parent_job.id}")
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
    
    @staticmethod
    async def _create_per_file_chain_jobs(
        parent_job: Job,
        chain_rules: List[Dict[str, str]],
        transfers: List[Transfer],
        db: AsyncSession
    ) -> List[Job]:
        """
        Create chain jobs for each successfully transferred file
        
        Args:
            parent_job: The parent job
            chain_rules: Chain rule definitions
            transfers: List of successful transfers with resolved destination paths
            db: Database session
            
        Returns:
            List of created chain jobs
        """
        created_jobs = []
        
        for transfer in transfers:
            # Use the actual destination path from the transfer
            actual_source_path = transfer.destination_path
            logger.info(f"Processing transfer {transfer.id} with destination_path: {actual_source_path}")
            
            # Strip remote prefix if present (e.g., "dest:path" -> "path")
            if actual_source_path and ':' in actual_source_path:
                # Split on first colon to remove remote prefix
                _, actual_source_path = actual_source_path.split(':', 1)
                logger.info(f"Stripped remote prefix from source path: {transfer.destination_path} -> {actual_source_path}")
            
            for idx, chain_rule in enumerate(chain_rules):
                try:
                    # Extract just the filename for the job name
                    import os
                    filename = os.path.basename(actual_source_path)
                    
                    # For chain jobs with specific files, use directory as source_path and filename as pattern
                    # This avoids the "can't limit to single files when using filters" error
                    dir_path = os.path.dirname(actual_source_path) if '/' in actual_source_path else ''
                    
                    # Create job data for this specific file
                    chain_job_data = JobCreate(
                        name=f"{parent_job.name} - {filename} - Chain {idx + 1}",
                        type=JobType.CHAINED,
                        source_endpoint_id=parent_job.destination_endpoint_id,
                        source_path=dir_path,  # Use directory path
                        destination_endpoint_id=chain_rule['endpoint_id'],
                        destination_path=ChainJobService._apply_path_template(
                            chain_rule['path_template'],
                            actual_source_path  # Apply template to actual path
                        ),
                        file_pattern=filename,  # Use filename as pattern
                        delete_source_after_transfer=False,
                        is_active=True,
                        config={
                            'parent_job_id': parent_job.id,
                            'parent_transfer_id': transfer.id,
                            'chain_index': idx,
                            'chain_rule': chain_rule,
                            'source_file': filename
                        }
                    )
                    
                    # Create the job
                    chain_job = Job(
                        id=str(uuid.uuid4()),
                        **chain_job_data.model_dump(),
                        parent_job_id=parent_job.id,
                        status=JobStatus.PENDING,
                        created_at=datetime.now(timezone.utc)
                    )
                    
                    db.add(chain_job)
                    created_jobs.append(chain_job)
                    
                    logger.info(
                        f"Created per-file chain job {chain_job.id} for file {filename} "
                        f"(parent job {parent_job.id})"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"Error creating chain job for transfer {transfer.id}: {e}"
                    )
                    continue
        
        if created_jobs:
            await db.commit()
            logger.info(f"Created {len(created_jobs)} per-file chain jobs")
            
        return created_jobs