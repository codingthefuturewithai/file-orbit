#!/usr/bin/env python3
"""
Create a transfer job from S3 to SMB share
"""
import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000/api/v1"

async def create_transfer():
    """Create S3 to SMB transfer job"""
    async with httpx.AsyncClient() as client:
        # First, get the endpoint IDs
        response = await client.get(f"{BASE_URL}/endpoints/")
        endpoints = response.json()
        
        # Find our endpoints
        s3_endpoint = next((ep for ep in endpoints if ep['name'] == "AWS S3 File Orbit Test Bucket"), None)
        smb_endpoint = next((ep for ep in endpoints if ep['name'] == "Test SMB Share"), None)
        
        if not s3_endpoint or not smb_endpoint:
            print("❌ Could not find required endpoints")
            return
            
        print(f"✅ Found S3 endpoint: {s3_endpoint['name']} (ID: {s3_endpoint['id']})")
        print(f"✅ Found SMB endpoint: {smb_endpoint['name']} (ID: {smb_endpoint['id']})")
        
        # Create the transfer job
        job_data = {
            "name": "S3 to Local SMB Transfer Test",
            "type": "manual",
            "source_endpoint_id": s3_endpoint['id'],
            "destination_endpoint_id": smb_endpoint['id'],
            "source_path": "/",  # Root of the bucket - adjust if needed
            "destination_path": "/test-transfer/",  # Will create this folder in the share
            "file_pattern": "*.mp4",  # Transfer only mp4 files - adjust as needed
            "delete_source_after_transfer": False,
            "is_active": True
        }
        
        print("\nCreating transfer job...")
        print(f"Source: S3 bucket '{s3_endpoint['config']['bucket']}'")
        print(f"Destination: SMB share '\\\\{smb_endpoint['config']['host']}\\{smb_endpoint['config']['share']}\\test-transfer'")
        print(f"File pattern: {job_data['file_pattern']}")
        
        response = await client.post(f"{BASE_URL}/jobs/", json=job_data)
        
        if response.status_code in [200, 201]:
            job = response.json()
            print(f"\n✅ Transfer job created successfully!")
            print(f"   Job ID: {job['id']}")
            print(f"   Status: {job['status']}")
            
            # Execute the job immediately
            print("\nExecuting the transfer...")
            exec_response = await client.post(f"{BASE_URL}/jobs/{job['id']}/execute")
            
            if exec_response.status_code == 200:
                print("✅ Transfer job has been queued for execution!")
                print("\nYou can monitor progress at: http://localhost:3000")
                print("Or check the worker logs in the terminal where worker.py is running")
            else:
                print(f"❌ Failed to execute job: {exec_response.status_code}")
                print(f"   Error: {exec_response.text}")
                
        else:
            print(f"❌ Failed to create job: {response.status_code}")
            print(f"   Error: {response.text}")

async def test_smb_connection():
    """Test the SMB endpoint connection first"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/endpoints/")
        endpoints = response.json()
        
        smb_endpoint = next((ep for ep in endpoints if ep['name'] == "Test SMB Share"), None)
        if smb_endpoint:
            print("Testing SMB connection...")
            test_response = await client.post(f"{BASE_URL}/endpoints/{smb_endpoint['id']}/test")
            result = test_response.json()
            if result.get('success'):
                print("✅ SMB connection test passed!")
            else:
                print(f"⚠️  SMB connection test failed: {result.get('message')}")
                print("The transfer may still work if rclone can connect.")

async def main():
    print("S3 to SMB Transfer Setup")
    print("=" * 50)
    
    # Test SMB connection first
    await test_smb_connection()
    
    print("\nReady to create the transfer job.")
    print("\nThis will transfer files from:")
    print("  Source: S3 bucket 'file-orbit-test-bucket'")
    print("  Destination: SMB share at 10.0.0.126/smb-test-mount/test-transfer/")
    
    confirm = input("\nProceed? (y/n): ")
    if confirm.lower() == 'y':
        await create_transfer()
    else:
        print("Transfer cancelled.")

if __name__ == "__main__":
    asyncio.run(main())