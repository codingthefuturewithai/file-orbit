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

async def seed_database():
    """Add sample data to the database"""
    async with AsyncSessionLocal() as session:
        await seed_endpoints(session)
        await seed_transfer_templates(session)
        await session.commit()
        print("Database seeded successfully!")

async def seed_endpoints(session: AsyncSession):
    """Add sample endpoints"""
    print("Adding sample endpoints...")
    
    endpoints = [
        Endpoint(
            id=str(uuid.uuid4()),
            name="Local Storage",
            type=EndpointType.LOCAL,
            config={"path": "/mnt/storage"},
            max_concurrent_transfers=10,
            is_active=True,
            connection_status="connected"
        ),
        Endpoint(
            id=str(uuid.uuid4()),
            name="5TB Limited Storage",
            type=EndpointType.LOCAL,
            config={"path": "/mnt/limited-storage"},
            max_concurrent_transfers=2,  # This is the throttled endpoint
            is_active=True,
            connection_status="connected"
        ),
        Endpoint(
            id=str(uuid.uuid4()),
            name="CTF S3 Bucket",
            type=EndpointType.S3,
            config={
                "bucket": "ctf-videos",
                "region": "us-east-1",
                "access_key": "YOUR_ACCESS_KEY",
                "secret_key": "YOUR_SECRET_KEY"
            },
            max_concurrent_transfers=5,
            is_active=True,
            connection_status="connected"
        ),
        Endpoint(
            id=str(uuid.uuid4()),
            name="Archive SMB Share",
            type=EndpointType.SMB,
            config={
                "host": "archive.ctf.org",
                "share": "videos",
                "user": "ctfuser",
                "domain": "CTF"
            },
            max_concurrent_transfers=3,
            is_active=True,
            connection_status="connected"
        )
    ]
    
    for endpoint in endpoints:
        session.add(endpoint)
    
    # Store endpoint IDs for transfer templates
    global local_id, limited_id, s3_id, smb_id
    local_id = endpoints[0].id
    limited_id = endpoints[1].id
    s3_id = endpoints[2].id
    smb_id = endpoints[3].id

async def seed_transfer_templates(session: AsyncSession):
    """Add sample transfer templates"""
    print("Adding sample transfer templates...")
    
    templates = [
        TransferTemplate(
            id=str(uuid.uuid4()),
            name="S3 to Local Transfer",
            description="Transfer new S3 videos to local storage",
            event_type=EventType.S3_OBJECT_CREATED,
            is_active=True,
            source_config={
                "bucket": "ctf-videos",
                "prefix": "incoming/",
                "suffix": ".mp4"
            },
            source_endpoint_id=s3_id,
            destination_endpoint_id=local_id,
            destination_path_template="/mnt/storage/videos/{year}/{month}/{filename}",
            chain_rules=[
                {
                    "endpoint_id": limited_id,
                    "path_template": "/mnt/limited-storage/archive/{year}/{filename}"
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
            name="Local File Watch",
            description="Watch for new files in upload directory",
            event_type=EventType.FILE_CREATED,
            is_active=True,
            source_config={
                "path": "/mnt/storage/uploads",
                "pattern": "*.mov",
                "recursive": True
            },
            source_endpoint_id=local_id,
            destination_endpoint_id=smb_id,
            destination_path_template="/processed/{year}/{month}/{day}/{filename}",
            file_pattern="*.mov",
            delete_source_after_transfer=True
        )
    ]
    
    for template in templates:
        session.add(template)

if __name__ == "__main__":
    asyncio.run(seed_database())