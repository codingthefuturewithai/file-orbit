#!/usr/bin/env python3
"""
Event monitoring service that watches for S3 events and file system changes
to trigger transfers based on transfer templates.
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
from app.services.redis_manager import redis_manager
from app.services.s3_event_monitor import S3EventMonitor
from app.services.file_watcher import FileWatcher
from app.models.transfer_template import EventType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('event_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EventMonitorService:
    """Main service that manages all event monitors"""
    
    def __init__(self):
        self.monitors = []
        self.running = False
        
        # Initialize Redis manager
        self.redis_manager = redis_manager
        
        # Configure AWS settings
        aws_config = {
            'access_key_id': settings.AWS_ACCESS_KEY_ID if hasattr(settings, 'AWS_ACCESS_KEY_ID') else None,
            'secret_access_key': settings.AWS_SECRET_ACCESS_KEY if hasattr(settings, 'AWS_SECRET_ACCESS_KEY') else None,
            'region': settings.AWS_REGION if hasattr(settings, 'AWS_REGION') else 'us-east-1',
            'monitored_buckets': []  # Will be loaded from transfer templates
        }
        
        # Initialize monitors
        self.s3_monitor = S3EventMonitor(self.redis_manager, aws_config)
        self.file_created_monitor = FileWatcher(self.redis_manager, EventType.FILE_CREATED)
        self.file_modified_monitor = FileWatcher(self.redis_manager, EventType.FILE_MODIFIED)
        
        self.monitors = [
            self.s3_monitor,
            self.file_created_monitor,
            self.file_modified_monitor
        ]
        
    async def start(self):
        """Start all event monitors"""
        if self.running:
            logger.warning("Event monitor service is already running")
            return
            
        self.running = True
        logger.info("Starting event monitor service")
        
        # Connect to Redis
        await self.redis_manager.connect()
        logger.info("Connected to Redis")
        
        # Start all monitors
        for monitor in self.monitors:
            try:
                await monitor.start()
                logger.info(f"Started {monitor.__class__.__name__}")
            except Exception as e:
                logger.error(f"Failed to start {monitor.__class__.__name__}: {e}")
                
        # Keep running until stopped
        while self.running:
            await asyncio.sleep(1)
            
    async def stop(self):
        """Stop all event monitors"""
        logger.info("Stopping event monitor service")
        self.running = False
        
        # Stop all monitors
        for monitor in self.monitors:
            try:
                await monitor.stop()
                logger.info(f"Stopped {monitor.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error stopping {monitor.__class__.__name__}: {e}")
                
    async def reload_configuration(self):
        """Reload configuration for all monitors"""
        logger.info("Reloading event monitor configuration")
        
        # Reload file watcher paths
        await self.file_created_monitor.reload_watch_paths()
        await self.file_modified_monitor.reload_watch_paths()
        
        # Reload S3 bucket configuration
        # This would reload from database in production
        logger.info("Configuration reloaded")


async def main():
    """Main entry point"""
    service = EventMonitorService()
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        asyncio.create_task(service.stop())
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())