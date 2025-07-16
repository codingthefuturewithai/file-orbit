#!/usr/bin/env python3
"""
WARNING: This script is DANGEROUS and should NOT be used!
It corrupts production endpoint data by overwriting it with test paths.

DO NOT RUN THIS SCRIPT - it will destroy your real endpoint configurations!

This script has been disabled to prevent data loss.
"""
import sys

print("ERROR: This script has been disabled because it corrupts production data!")
print("It overwrites real endpoint configurations with test paths.")
print("DO NOT USE THIS SCRIPT.")
sys.exit(1)

# ORIGINAL DANGEROUS CODE BELOW - DO NOT UNCOMMENT
"""
import asyncio
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.endpoint import Endpoint, EndpointType

async def update_endpoints():
    """Update endpoints to use test paths"""
    async with AsyncSessionLocal() as db:
        # Get all endpoints
        result = await db.execute(select(Endpoint))
        endpoints = result.scalars().all()
        
        print("Updating endpoints for testing...")
        
        for endpoint in endpoints:
            if endpoint.type == EndpointType.LOCAL:
                if "5TB" in endpoint.name:
                    # Update 5TB limited storage
                    endpoint.config = {"path": "/tmp/ctf-rclone-test/5tb-limited"}
                    print(f"Updated {endpoint.name} to use /tmp/ctf-rclone-test/5tb-limited")
                else:
                    # Update regular local storage
                    endpoint.config = {"path": "/tmp/ctf-rclone-test/source"}
                    print(f"Updated {endpoint.name} to use /tmp/ctf-rclone-test/source")
            
            elif endpoint.type == EndpointType.SMB:
                # For testing, we'll use a local path instead of actual SMB
                endpoint.type = EndpointType.LOCAL
                endpoint.config = {"path": "/tmp/ctf-rclone-test/archive"}
                print(f"Updated {endpoint.name} to use local path /tmp/ctf-rclone-test/archive (for testing)")
            
            # Keep S3 endpoint as is (requires real credentials)
            # In a real test, you'd update this with test bucket info
        
        await db.commit()
        print("\nEndpoints updated for testing!")
        print("\nTest paths:")
        print("- Source: /tmp/ctf-rclone-test/source")
        print("- 5TB Limited: /tmp/ctf-rclone-test/5tb-limited")
        print("- Archive: /tmp/ctf-rclone-test/archive")
        print("- Destination: /tmp/ctf-rclone-test/dest")
        print("\nYou can now create transfers between these endpoints.")

# if __name__ == "__main__":
#     asyncio.run(update_endpoints())
"""