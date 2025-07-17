#!/usr/bin/env python3
"""
Comprehensive script to fix all data issues in one shot
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.append(str(Path(__file__).parent))

from sqlalchemy import select, update, delete
from app.core.database import AsyncSessionLocal
from app.models.endpoint import Endpoint, EndpointType
from app.models.job import Job, JobStatus

async def fix_all_data():
    """Fix all data issues comprehensively"""
    async with AsyncSessionLocal() as db:
        print("=== FIXING ALL DATA ISSUES ===\n")
        
        # 1. Fix corrupted SMB endpoints
        print("1. Fixing corrupted endpoints...")
        result = await db.execute(select(Endpoint))
        endpoints = result.scalars().all()
        
        fixed_count = 0
        for endpoint in endpoints:
            # Check for corruption: LOCAL type but has SMB fields
            if endpoint.type == EndpointType.LOCAL and any(key in endpoint.config for key in ['host', 'share', 'user', 'password', 'domain']):
                print(f"   Fixing: {endpoint.name}")
                
                # Extract SMB fields and remove local path
                new_config = {}
                for key in ['host', 'share', 'user', 'password', 'domain']:
                    if key in endpoint.config:
                        new_config[key] = endpoint.config[key]
                
                # Ensure domain has a default
                if 'domain' not in new_config or not new_config['domain']:
                    new_config['domain'] = 'WORKGROUP'
                
                # Update the endpoint
                await db.execute(
                    update(Endpoint)
                    .where(Endpoint.id == endpoint.id)
                    .values(
                        type=EndpointType.SMB,
                        config=new_config,
                        updated_at=datetime.now(timezone.utc)
                    )
                )
                fixed_count += 1
                print("     - Changed type to SMB")
                print("     - Cleaned config to only SMB fields")
        
        print(f"   Fixed {fixed_count} corrupted endpoints\n")
        
        # 2. Delete any TEST_ endpoints created by safe script
        print("2. Cleaning up test endpoints...")
        result = await db.execute(
            select(Endpoint).where(Endpoint.name.like("TEST_%"))
        )
        test_endpoints = result.scalars().all()
        
        if test_endpoints:
            for ep in test_endpoints:
                print(f"   Deleting: {ep.name}")
                await db.delete(ep)
            print(f"   Deleted {len(test_endpoints)} test endpoints\n")
        else:
            print("   No test endpoints found\n")
        
        # 3. Fix any remaining PENDING jobs (cleanup)
        print("3. Cleaning up old PENDING jobs...")
        result = await db.execute(
            select(Job).where(Job.status == JobStatus.PENDING)
        )
        pending_jobs = result.scalars().all()
        
        if pending_jobs:
            await db.execute(
                delete(Job).where(Job.status == JobStatus.PENDING)
            )
            print(f"   Deleted {len(pending_jobs)} old PENDING jobs\n")
        else:
            print("   No PENDING jobs found\n")
        
        # Commit all changes
        await db.commit()
        
        # 4. Verify the fixes
        print("4. Verifying fixes...")
        
        # Check SMB Destination Share
        result = await db.execute(
            select(Endpoint).where(Endpoint.name == "SMB Destination Share")
        )
        smb_endpoint = result.scalar_one_or_none()
        
        if smb_endpoint:
            print("   SMB Destination Share:")
            print(f"     - Type: {smb_endpoint.type}")
            print(f"     - Host: {smb_endpoint.config.get('host')}")
            print(f"     - Share: {smb_endpoint.config.get('share')}")
            print(f"     - User: {smb_endpoint.config.get('user')}")
            print(f"     - Domain: {smb_endpoint.config.get('domain')}")
            print(f"     - Has 'path' field: {'path' in smb_endpoint.config}")
            
            if smb_endpoint.type == EndpointType.SMB and 'path' not in smb_endpoint.config:
                print("     ✓ VERIFIED: Endpoint is correctly configured as SMB")
            else:
                print("     ✗ ERROR: Endpoint still has issues!")
                return False
        else:
            print("   ERROR: SMB Destination Share not found!")
            return False
        
        print("\n=== ALL DATA ISSUES FIXED SUCCESSFULLY ===")
        return True

if __name__ == "__main__":
    success = asyncio.run(fix_all_data())
    sys.exit(0 if success else 1)