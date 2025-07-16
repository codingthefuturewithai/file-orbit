"""
Base event monitoring service for handling event-driven transfers
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.transfer_template import TransferTemplate, EventType
from app.models.job import Job, JobType, JobStatus
from app.schemas.job import JobCreate
from app.services.redis_manager import RedisManager
# from app.services.chain_job_service import ChainJobService  # PHASE 3: Now handled by worker

logger = logging.getLogger(__name__)


class EventMonitor(ABC):
    """Base class for event monitoring services"""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager
        self.running = False
        self._tasks: List[asyncio.Task] = []
        
    @abstractmethod
    async def start(self):
        """Start monitoring for events"""
        pass
        
    @abstractmethod
    async def stop(self):
        """Stop monitoring for events"""
        pass
        
    @abstractmethod
    def get_event_type(self) -> EventType:
        """Get the event type this monitor handles"""
        pass
        
    async def process_event(self, event_data: Dict[str, Any]):
        """Process an incoming event and trigger transfers"""
        event_type = self.get_event_type()
        logger.info(f"Processing {event_type} event: {event_data}")
        
        # Get matching transfer templates from database
        async for db in get_db():
            try:
                result = await db.execute(
                    select(TransferTemplate).where(
                        TransferTemplate.event_type == event_type,
                        TransferTemplate.is_active == True
                    )
                )
                templates = result.scalars().all()
                
                for template in templates:
                    if self._matches_template(event_data, template):
                        await self._trigger_transfer(template, event_data, db)
                        
            except Exception as e:
                logger.error(f"Error processing event: {e}")
            finally:
                await db.close()
                
    def _matches_template(self, event_data: Dict[str, Any], template: TransferTemplate) -> bool:
        """Check if event matches transfer template criteria"""
        # Check file pattern
        file_path = event_data.get('file_path', '')
        file_name = file_path.split('/')[-1] if file_path else ''
        
        if template.file_pattern and template.file_pattern != '*':
            import fnmatch
            if not fnmatch.fnmatch(file_name, template.file_pattern):
                return False
                
        # Check source configuration
        if template.source_config:
            # For S3 events, check bucket and prefix
            if template.event_type == EventType.S3_OBJECT_CREATED:
                bucket = event_data.get('bucket')
                key = event_data.get('key', '')
                
                if template.source_config.get('bucket_name') and bucket != template.source_config['bucket_name']:
                    return False
                    
                prefix = template.source_config.get('prefix')
                if prefix and not key.startswith(prefix):
                    return False
                    
            # For file events, check watch path
            elif template.event_type in [EventType.FILE_CREATED, EventType.FILE_MODIFIED]:
                watch_path = template.source_config.get('watch_path')
                if watch_path and not file_path.startswith(watch_path):
                    return False
                    
        return True
        
    async def _trigger_transfer(self, template: TransferTemplate, event_data: Dict[str, Any], db: AsyncSession):
        """Create a job for the matched transfer template"""
        try:
            # Build source and destination paths
            source_path = event_data.get('file_path', '')
            
            # Apply destination path template
            dest_path = self._apply_path_template(
                template.destination_path_template,
                source_path,
                event_data
            )
            
            # Create job
            job_data = JobCreate(
                name=f"{template.name} - {source_path.split('/')[-1]}",
                type=JobType.EVENT_TRIGGERED,
                source_endpoint_id=template.source_endpoint_id,
                source_path=source_path,
                destination_endpoint_id=template.destination_endpoint_id,
                destination_path=dest_path,
                file_pattern=template.file_pattern or '*',
                delete_source_after_transfer=template.delete_source_after_transfer,
                is_active=True,
                config={
                    'transfer_template_id': template.id,
                    'event_data': event_data,
                    'chain_rules': template.chain_rules
                }
            )
            
            job = Job(
                id=str(uuid.uuid4()),
                **job_data.model_dump(),
                status=JobStatus.QUEUED,
                created_at=datetime.now(timezone.utc)
            )
            
            db.add(job)
            await db.commit()
            
            # Queue the job for processing
            await self.redis_manager.enqueue_job(job.id)
            
            # Update template statistics
            template.total_triggers += 1
            template.last_triggered = datetime.now(timezone.utc)
            await db.commit()
            
            logger.info(f"Created job {job.id} for event template {template.name}")
            
            # PHASE 3: Chain jobs are now created by worker after successful transfers
            # Event-driven transfers typically handle single files, so this works well
                
        except Exception as e:
            logger.error(f"Error triggering transfer for template {template.name}: {e}")
            await db.rollback()
            
    def _apply_path_template(self, template: str, source_path: str, event_data: Dict[str, Any]) -> str:
        """Apply variables to destination path template"""
        import os
        from datetime import datetime
        
        filename = os.path.basename(source_path)
        name_without_ext, ext = os.path.splitext(filename)
        now = datetime.now()
        
        replacements = {
            '{filename}': filename,
            '{original_filename}': filename,  # Alias for {filename}
            '{name}': name_without_ext,
            '{ext}': ext,
            '{year}': str(now.year),
            '{month}': f"{now.month:02d}",
            '{day}': f"{now.day:02d}",
            '{hour}': f"{now.hour:02d}",
            '{minute}': f"{now.minute:02d}",
            '{timestamp}': str(int(now.timestamp())),
        }
        
        result = template
        for key, value in replacements.items():
            result = result.replace(key, value)
            
        return result