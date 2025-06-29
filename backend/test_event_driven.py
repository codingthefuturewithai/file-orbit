#!/usr/bin/env python3
"""
Test script for event-driven transfers
Creates test transfer templates and triggers file system events
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import shutil

sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.models.transfer_template import TransferTemplate, EventType
from app.models.endpoint import Endpoint
from sqlalchemy import select


async def setup_test_transfer_templates():
    """Create test transfer templates for file watching"""
    async with AsyncSessionLocal() as db:
        # Get endpoints
        result = await db.execute(
            select(Endpoint).where(Endpoint.name == "Local Storage")
        )
        local_storage = result.scalar_one_or_none()
        
        result = await db.execute(
            select(Endpoint).where(Endpoint.name == "5TB Limited Storage")
        )
        limited_storage = result.scalar_one_or_none()
        
        if not local_storage or not limited_storage:
            print("Error: Required endpoints not found. Run setup_test_data.py first")
            return False
            
        # Create watch directory
        watch_dir = "/tmp/ctf-rclone-test/watch"
        os.makedirs(watch_dir, exist_ok=True)
        
        # Check if template already exists
        result = await db.execute(
            select(TransferTemplate).where(TransferTemplate.name == "Test File Watcher")
        )
        existing_rule = result.scalar_one_or_none()
        
        if not existing_rule:
            # Create file watcher template
            file_watch_rule = TransferTemplate(
                id="test-file-watch-001",
                name="Test File Watcher",
                description="Watches for new MP4 files in test directory",
                event_type=EventType.FILE_CREATED,
                source_endpoint_id=local_storage.id,
                destination_endpoint_id=limited_storage.id,
                destination_path_template="/event-triggered/{year}/{month}/{filename}",
                file_pattern="*.mp4",
                delete_source_after_transfer=False,
                is_active=True,
                source_config={
                    "watch_path": watch_dir
                }
            )
            
            db.add(file_watch_rule)
            await db.commit()
            print(f"Created file watcher rule: {file_watch_rule.name}")
            
        # Create chain rule example
        result = await db.execute(
            select(Endpoint).where(Endpoint.name == "Archive SMB Share")
        )
        archive_endpoint = result.scalar_one_or_none()
        
        if archive_endpoint:
            result = await db.execute(
                select(TransferTemplate).where(TransferTemplate.name == "Test Chain Transfer")
            )
            existing_chain = result.scalar_one_or_none()
            
            if not existing_chain:
                chain_rule = TransferTemplate(
                    id="test-chain-001",
                    name="Test Chain Transfer",
                    description="Transfers with chain to archive",
                    event_type=EventType.FILE_CREATED,
                    source_endpoint_id=local_storage.id,
                    destination_endpoint_id=limited_storage.id,
                    destination_path_template="/primary/{filename}",
                    file_pattern="*.mxf",
                    delete_source_after_transfer=False,
                    is_active=True,
                    source_config={
                        "watch_path": watch_dir
                    },
                    chain_rules=[
                        {
                            "endpoint_id": archive_endpoint.id,
                            "path_template": "/archive/{year}/{month}/{filename}"
                        }
                    ]
                )
                
                db.add(chain_rule)
                await db.commit()
                print(f"Created chain transfer rule: {chain_rule.name}")
                
        return True


async def trigger_file_events():
    """Create test files to trigger events"""
    watch_dir = "/tmp/ctf-rclone-test/watch"
    source_dir = "/tmp/ctf-rclone-test/source"
    
    print(f"\nCreating test files in {watch_dir}")
    
    # Create MP4 file (triggers simple transfer)
    test_mp4 = os.path.join(source_dir, "test_event_video.mp4")
    if os.path.exists(test_mp4):
        dest_mp4 = os.path.join(watch_dir, f"event_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
        shutil.copy2(test_mp4, dest_mp4)
        print(f"Created: {dest_mp4}")
        
    # Create MXF file (triggers chain transfer)
    test_mxf = os.path.join(watch_dir, f"chain_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mxf")
    with open(test_mxf, 'w') as f:
        f.write("Test MXF content for chain transfer")
    print(f"Created: {test_mxf}")
    
    print("\nFiles created. The event monitor should detect these and create transfer jobs.")
    print("Check the worker logs to see the transfers being processed.")


async def main():
    """Main test function"""
    print("Setting up event-driven transfer test...")
    
    # Setup transfer templates
    success = await setup_test_transfer_templates()
    if not success:
        return
        
    print("\nEvent rules created successfully!")
    print("\nTo test event-driven transfers:")
    print("1. Start the event monitor: python event_monitor_service.py")
    print("2. Start the worker: python worker.py")
    print("3. Run this script again with --trigger flag")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--trigger":
        await trigger_file_events()


if __name__ == "__main__":
    asyncio.run(main())