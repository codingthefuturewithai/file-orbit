#!/usr/bin/env python3
"""
Fix the corrupted SMB Destination Share endpoint
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.endpoint import Endpoint, EndpointType

async def fix_smb_endpoint():
    """Fix the SMB Destination Share endpoint"""
    async with AsyncSessionLocal() as db:
        # Get the endpoint
        result = await db.execute(
            select(Endpoint).where(Endpoint.name == "SMB Destination Share")
        )
        endpoint = result.scalar_one_or_none()
        
        if not endpoint:
            print("ERROR: SMB Destination Share endpoint not found!")
            return
        
        print("Current state:")
        print(f"  Type: {endpoint.type}")
        print(f"  Config: {endpoint.config}")
        
        # Fix the endpoint
        if endpoint.type == EndpointType.LOCAL and 'host' in endpoint.config:
            print("\nFixing endpoint...")
            
            # Update type to SMB and clean config
            new_config = {
                'host': endpoint.config.get('host'),
                'share': endpoint.config.get('share'),
                'user': endpoint.config.get('user'),
                'password': endpoint.config.get('password'),
                'domain': endpoint.config.get('domain', 'WORKGROUP')
            }
            
            # Remove any local path field
            if 'path' in new_config:
                del new_config['path']
            
            await db.execute(
                update(Endpoint)
                .where(Endpoint.id == endpoint.id)
                .values(
                    type=EndpointType.SMB,
                    config=new_config
                )
            )
            await db.commit()
            
            print("Endpoint fixed!")
            print("  New Type: SMB")
            print(f"  New Config: {new_config}")
        else:
            print("\nEndpoint doesn't need fixing or already fixed.")

if __name__ == "__main__":
    asyncio.run(fix_smb_endpoint())