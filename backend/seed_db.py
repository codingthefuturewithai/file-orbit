#!/usr/bin/env python3
"""
Seed the database with sample data for testing.
Run this after init_db.py to populate with test data.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import uuid

sys.path.append(str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models import Endpoint, TransferTemplate
from app.models.endpoint import EndpointType
from app.models.transfer_template import EventType
from app.services.settings_service import SettingsService

async def seed_database():
    """Add sample data to the database"""
    async with AsyncSessionLocal() as session:
        await seed_endpoints(session)
        await seed_transfer_templates(session)
        await session.commit()
        
        # Initialize settings
        print("\nInitializing application settings...")
        await SettingsService.initialize_settings(session)
        
        print("\n✅ Database seeded successfully!")
        print("\n📝 Note: Example endpoints and templates have been created.")
        print("   - Local endpoints use /tmp/file-orbit/ paths (safe for testing)")
        print("   - S3 and SMB endpoints are disabled until you add credentials")
        print("   - Update the endpoints in the UI to match your environment")
        print("   - Application settings have been initialized with default values")
        print("\n🚀 You can now access the UI at http://localhost:3000")

async def seed_endpoints(session: AsyncSession):
    """Add sample endpoints"""
    print("Adding sample endpoints...")
    
    endpoints = [
        Endpoint(
            id=str(uuid.uuid4()),
            name="Example: Local Storage",
            type=EndpointType.LOCAL,
            config={"path": "/tmp/file-orbit/local-storage"},
            max_concurrent_transfers=10,
            is_active=True,
            connection_status="connected"
        ),
        Endpoint(
            id=str(uuid.uuid4()),
            name="Example: Throttled Storage (2 concurrent)",
            type=EndpointType.LOCAL,
            config={"path": "/tmp/file-orbit/throttled-storage"},
            max_concurrent_transfers=2,  # This is the throttled endpoint
            is_active=True,
            connection_status="connected"
        ),
        Endpoint(
            id=str(uuid.uuid4()),
            name="Example: AWS S3 Bucket",
            type=EndpointType.S3,
            config={
                "bucket": "your-bucket-name",
                "region": "us-east-1",
                "access_key": "YOUR_ACCESS_KEY",
                "secret_key": "YOUR_SECRET_KEY"
            },
            max_concurrent_transfers=5,
            is_active=False,  # Disabled by default until configured
            connection_status="not_configured"
        ),
        Endpoint(
            id=str(uuid.uuid4()),
            name="Example: SMB/CIFS Share",
            type=EndpointType.SMB,
            config={
                "host": "fileserver.example.com",
                "share": "shared-folder",
                "user": "your-username",
                "password": "your-password",
                "domain": "WORKGROUP"
            },
            max_concurrent_transfers=3,
            is_active=False,  # Disabled by default until configured
            connection_status="not_configured"
        ),
        Endpoint(
            id=str(uuid.uuid4()),
            name="Example: SFTP Server",
            type=EndpointType.SFTP,
            config={
                "host": "sftp.example.com",
                "port": 22,
                "user": "your-username",
                "password": "your-password",
                # For SSH key auth, use these instead:
                # "key_file": "/home/user/.ssh/id_rsa",
                # "key_passphrase": "passphrase-if-needed"
            },
            max_concurrent_transfers=3,
            is_active=False,  # Disabled by default until configured
            connection_status="not_configured"
        )
    ]
    
    for endpoint in endpoints:
        session.add(endpoint)
    
    # Store endpoint IDs for transfer templates
    global local_id, limited_id, s3_id, smb_id, sftp_id
    local_id = endpoints[0].id
    limited_id = endpoints[1].id
    s3_id = endpoints[2].id
    smb_id = endpoints[3].id
    sftp_id = endpoints[4].id

async def seed_transfer_templates(session: AsyncSession):
    """Add sample transfer templates"""
    print("Adding sample transfer templates...")
    
    templates = [
        TransferTemplate(
            id=str(uuid.uuid4()),
            name="Example: S3 Event-Driven Transfer",
            description="Example template for S3 → Local → Archive workflow. Configure S3 endpoint and update paths before activating.",
            event_type=EventType.S3_OBJECT_CREATED,
            is_active=False,  # Disabled until S3 is configured
            source_config={
                "bucket": "your-bucket-name",
                "prefix": "incoming/",
                "suffix": ".mp4"
            },
            source_endpoint_id=s3_id,
            destination_endpoint_id=local_id,
            destination_path_template="/tmp/file-orbit/videos/{year}/{month}/{filename}",
            chain_rules=[
                {
                    "endpoint_id": limited_id,
                    "path_template": "/tmp/file-orbit/archive/{year}/{filename}"
                },
                {
                    "endpoint_id": smb_id,
                    "path_template": "/backup/{year}/{month}/{filename}"
                }
            ],
            file_pattern="*.mp4",
            delete_source_after_transfer=False
        ),
        TransferTemplate(
            id=str(uuid.uuid4()),
            name="Example: Local Directory Watcher",
            description="Example template that watches a local directory for new files. Update the watch path and destination before activating.",
            event_type=EventType.FILE_CREATED,
            is_active=False,  # Disabled by default
            source_config={
                "path": "/tmp/file-orbit/uploads",
                "pattern": "*.mov",
                "recursive": True
            },
            source_endpoint_id=local_id,
            destination_endpoint_id=local_id,  # Changed to local since SMB is disabled
            destination_path_template="/tmp/file-orbit/processed/{year}/{month}/{day}/{filename}",
            file_pattern="*.mov",
            delete_source_after_transfer=False  # Changed to false for safety
        )
    ]
    
    for template in templates:
        session.add(template)

if __name__ == "__main__":
    asyncio.run(seed_database())