"""
S3 event monitoring service for handling S3 ObjectCreated events
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import aioboto3
from botocore.exceptions import ClientError

from app.models.transfer_template import EventType
from app.services.event_monitor import EventMonitor
from app.services.redis_manager import RedisManager

logger = logging.getLogger(__name__)


class S3EventMonitor(EventMonitor):
    """Monitor S3 buckets for object creation events"""
    
    def __init__(self, redis_manager: RedisManager, aws_config: Optional[Dict[str, Any]] = None):
        super().__init__(redis_manager)
        self.aws_config = aws_config or {}
        self.session = aioboto3.Session(
            aws_access_key_id=self.aws_config.get('access_key_id'),
            aws_secret_access_key=self.aws_config.get('secret_access_key'),
            region_name=self.aws_config.get('region', 'us-east-1')
        )
        self._polling_interval = 30  # Poll every 30 seconds
        self._processed_events = set()  # Track processed events to avoid duplicates
        
    def get_event_type(self) -> EventType:
        return EventType.S3_OBJECT_CREATED
        
    async def start(self):
        """Start monitoring S3 buckets for events"""
        if self.running:
            logger.warning("S3 event monitor is already running")
            return
            
        self.running = True
        logger.info("Starting S3 event monitor")
        
        # Start monitoring task
        monitor_task = asyncio.create_task(self._monitor_loop())
        self._tasks.append(monitor_task)
        
    async def stop(self):
        """Stop monitoring S3 events"""
        logger.info("Stopping S3 event monitor")
        self.running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                await self._check_s3_events()
            except Exception as e:
                logger.error(f"Error in S3 monitoring loop: {e}")
                
            # Wait before next check
            await asyncio.sleep(self._polling_interval)
            
    async def _check_s3_events(self):
        """Check for new S3 events"""
        # In a real implementation, this would:
        # 1. Poll SQS queue for S3 event notifications
        # 2. Or use S3 Event Notifications with SNS/SQS
        # 3. Or poll S3 buckets directly for new objects
        
        # For MVP, we'll simulate by checking configured buckets
        async with self.session.client('s3') as s3:
            # Get list of buckets to monitor from configuration
            buckets = self.aws_config.get('monitored_buckets', [])
            
            for bucket_config in buckets:
                bucket_name = bucket_config.get('name')
                prefix = bucket_config.get('prefix', '')
                
                if not bucket_name:
                    continue
                    
                try:
                    # List objects in bucket
                    response = await s3.list_objects_v2(
                        Bucket=bucket_name,
                        Prefix=prefix,
                        MaxKeys=100
                    )
                    
                    if 'Contents' not in response:
                        continue
                        
                    for obj in response['Contents']:
                        # Check if we've already processed this object
                        event_id = f"{bucket_name}:{obj['Key']}:{obj['ETag']}"
                        if event_id in self._processed_events:
                            continue
                            
                        # Check if object is new (created in last polling interval)
                        last_modified = obj['LastModified']
                        if hasattr(last_modified, 'timestamp'):
                            age_seconds = (datetime.now().timestamp() - last_modified.timestamp())
                            if age_seconds > self._polling_interval * 2:
                                # Object is too old, skip
                                continue
                                
                        # Process new object event
                        event_data = {
                            'bucket': bucket_name,
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'etag': obj['ETag'],
                            'last_modified': obj['LastModified'].isoformat() if hasattr(obj['LastModified'], 'isoformat') else str(obj['LastModified']),
                            'file_path': f"s3://{bucket_name}/{obj['Key']}",
                            'event_time': datetime.now().isoformat()
                        }
                        
                        await self.process_event(event_data)
                        self._processed_events.add(event_id)
                        
                        # Limit processed events cache size
                        if len(self._processed_events) > 10000:
                            # Remove oldest entries
                            self._processed_events = set(list(self._processed_events)[-5000:])
                            
                except ClientError as e:
                    logger.error(f"Error accessing bucket {bucket_name}: {e}")
                    
    async def setup_bucket_notifications(self, bucket_name: str, notification_config: Dict[str, Any]):
        """Setup S3 bucket notifications (for future use with SQS/SNS)"""
        async with self.session.client('s3') as s3:
            try:
                # This would configure S3 Event Notifications
                # For MVP, we're using polling instead
                logger.info(f"Bucket notifications would be configured for {bucket_name}")
                
            except ClientError as e:
                logger.error(f"Error setting up bucket notifications: {e}")
                raise