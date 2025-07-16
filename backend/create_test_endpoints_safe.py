#!/usr/bin/env python3
"""
SAFE script to create TEST-ONLY endpoints for testing.
This script creates NEW endpoints with "TEST_" prefix and does NOT modify any existing endpoints.
"""
import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone

sys.path.append(str(Path(__file__).parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.endpoint import Endpoint, EndpointType

async def create_test_endpoints():
    """Create test-only endpoints without touching existing data"""
    async with AsyncSessionLocal() as db:
        # Check if test endpoints already exist
        result = await db.execute(
            select(Endpoint).where(Endpoint.name.like("TEST_%"))
        )
        existing_test_endpoints = result.scalars().all()
        
        if existing_test_endpoints:
            print("Test endpoints already exist:")
            for ep in existing_test_endpoints:
                print(f"  - {ep.name}")
            
            response = input("\nDelete existing test endpoints and recreate? (y/N): ")
            if response.lower() == 'y':
                for ep in existing_test_endpoints:
                    await db.delete(ep)
                await db.commit()
                print("Deleted existing test endpoints.")
            else:
                print("Keeping existing test endpoints.")
                return
        
        print("Creating SAFE test endpoints (will NOT modify your real endpoints)...")
        
        # Create test endpoints
        test_endpoints = [
            {
                "id": str(uuid.uuid4()),
                "name": "TEST_Local_Source",
                "type": EndpointType.LOCAL,
                "config": {"path": "/tmp/ctf-rclone-test/source"},
                "created_at": datetime.now(timezone.utc),
                "updated_at": None
            },
            {
                "id": str(uuid.uuid4()),
                "name": "TEST_Local_Destination",
                "type": EndpointType.LOCAL,
                "config": {"path": "/tmp/ctf-rclone-test/dest"},
                "created_at": datetime.now(timezone.utc),
                "updated_at": None
            },
            {
                "id": str(uuid.uuid4()),
                "name": "TEST_Local_Archive",
                "type": EndpointType.LOCAL,
                "config": {"path": "/tmp/ctf-rclone-test/archive"},
                "created_at": datetime.now(timezone.utc),
                "updated_at": None
            },
            {
                "id": str(uuid.uuid4()),
                "name": "TEST_SMB_Share",
                "type": EndpointType.SMB,
                "config": {
                    "host": "test-server.example.com",
                    "share": "test-share",
                    "user": "testuser",
                    "domain": "TESTDOMAIN",
                    "password": "test-password"
                },
                "created_at": datetime.now(timezone.utc),
                "updated_at": None
            }
        ]
        
        for endpoint_data in test_endpoints:
            endpoint = Endpoint(**endpoint_data)
            db.add(endpoint)
            print(f"Created: {endpoint.name} (Type: {endpoint.type.value})")
        
        await db.commit()
        
        print("\nTest endpoints created successfully!")
        print("These endpoints have 'TEST_' prefix and will not interfere with your real endpoints.")
        print("\nYour production endpoints remain unchanged.")

if __name__ == "__main__":
    asyncio.run(create_test_endpoints())