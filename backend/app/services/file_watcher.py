"""
File system watcher service for monitoring local file changes
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Any, Set, Optional
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

from app.models.transfer_template import EventType
from app.services.event_monitor import EventMonitor
from app.services.redis_manager import RedisManager

logger = logging.getLogger(__name__)


class FileEventHandler(FileSystemEventHandler):
    """Handle file system events"""
    
    def __init__(self, event_queue: asyncio.Queue, event_type: EventType):
        self.event_queue = event_queue
        self.event_type = event_type
        
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory and self.event_type == EventType.FILE_CREATED:
            self._queue_event(event)
            
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory and self.event_type == EventType.FILE_MODIFIED:
            self._queue_event(event)
            
    def _queue_event(self, event):
        """Queue event for processing"""
        try:
            # Get file info
            file_path = event.src_path
            file_stat = os.stat(file_path)
            
            event_data = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_size': file_stat.st_size,
                'modified_time': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                'event_type': self.event_type.value,
                'event_time': datetime.now().isoformat()
            }
            
            # Put event in queue (non-blocking)
            self.event_queue.put_nowait(event_data)
            
        except Exception as e:
            logger.error(f"Error queuing file event: {e}")


class FileWatcher(EventMonitor):
    """Monitor file system for file creation/modification events"""
    
    def __init__(self, redis_manager: RedisManager, event_type: EventType = EventType.FILE_CREATED):
        super().__init__(redis_manager)
        self.event_type = event_type
        self.observer = Observer()
        self.watched_paths: Set[str] = set()
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._processor_task: Optional[asyncio.Task] = None
        
    def get_event_type(self) -> EventType:
        return self.event_type
        
    async def start(self):
        """Start monitoring file system"""
        if self.running:
            logger.warning(f"File watcher for {self.event_type} is already running")
            return
            
        self.running = True
        logger.info(f"Starting file watcher for {self.event_type}")
        
        # Load watch paths from transfer templates
        await self._load_watch_paths()
        
        # Start the observer
        self.observer.start()
        
        # Start event processor
        self._processor_task = asyncio.create_task(self._process_events())
        self._tasks.append(self._processor_task)
        
    async def stop(self):
        """Stop monitoring file system"""
        logger.info(f"Stopping file watcher for {self.event_type}")
        self.running = False
        
        # Stop the observer
        self.observer.stop()
        self.observer.join(timeout=5)
        
        # Cancel processor task
        if self._processor_task:
            self._processor_task.cancel()
            
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
            
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
    async def _load_watch_paths(self):
        """Load paths to watch from active transfer templates"""
        from sqlalchemy import select
        from app.core.database import get_db
        from app.models.transfer_template import TransferTemplate
        
        async for db in get_db():
            try:
                result = await db.execute(
                    select(TransferTemplate).where(
                        TransferTemplate.event_type == self.event_type,
                        TransferTemplate.is_active == True
                    )
                )
                rules = result.scalars().all()
                
                for rule in rules:
                    if rule.source_config and 'watch_path' in rule.source_config:
                        watch_path = rule.source_config['watch_path']
                        self.add_watch_path(watch_path)
                        
            except Exception as e:
                logger.error(f"Error loading watch paths: {e}")
            finally:
                await db.close()
                
    def add_watch_path(self, path: str):
        """Add a path to watch"""
        if path in self.watched_paths:
            return
            
        # Ensure path exists
        watch_path = Path(path)
        if not watch_path.exists():
            logger.warning(f"Watch path does not exist: {path}")
            watch_path.mkdir(parents=True, exist_ok=True)
            
        # Create event handler
        event_handler = FileEventHandler(self.event_queue, self.event_type)
        
        # Schedule observer
        self.observer.schedule(event_handler, path, recursive=True)
        self.watched_paths.add(path)
        
        logger.info(f"Added watch path: {path} for {self.event_type}")
        
    def remove_watch_path(self, path: str):
        """Remove a path from watching"""
        if path not in self.watched_paths:
            return
            
        # Unschedule from observer
        for handler in self.observer._handlers:
            if handler._watch.path == path:
                self.observer.unschedule(handler)
                break
                
        self.watched_paths.discard(path)
        logger.info(f"Removed watch path: {path}")
        
    async def _process_events(self):
        """Process events from the queue"""
        while self.running:
            try:
                # Wait for events with timeout
                event_data = await asyncio.wait_for(
                    self.event_queue.get(), 
                    timeout=1.0
                )
                
                # Process the event
                await self.process_event(event_data)
                
            except asyncio.TimeoutError:
                # No events, continue
                continue
            except Exception as e:
                logger.error(f"Error processing file event: {e}")
                
    async def reload_watch_paths(self):
        """Reload watch paths (useful when transfer templates change)"""
        # Clear existing watches
        for path in list(self.watched_paths):
            self.remove_watch_path(path)
            
        # Reload from database
        await self._load_watch_paths()