#!/usr/bin/env python3
"""
Quick test to verify SMB/SFTP endpoint creation through the API
"""
import httpx
import asyncio

BASE_URL = "http://localhost:8000/api/v1"

async def create_test_endpoints():
    """Create test SMB and SFTP endpoints via API"""
    async with httpx.AsyncClient() as client:
        # Create SMB endpoint
        smb_endpoint = {
            "name": "Test SMB Share",
            "type": "smb",
            "config": {
                "host": "192.168.1.100",
                "user": "testuser",
                "password": "testpass",
                "domain": "WORKGROUP"
            },
            "max_concurrent_transfers": 3,
            "is_active": True
        }
        
        print("Creating SMB endpoint...")
        response = await client.post(f"{BASE_URL}/endpoints/", json=smb_endpoint)
        if response.status_code == 200:
            print("✅ SMB endpoint created successfully")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Failed to create SMB endpoint: {response.status_code}")
            print(f"   Error: {response.text}")
        
        # Create SFTP endpoint
        sftp_endpoint = {
            "name": "Test SFTP Server",
            "type": "sftp", 
            "config": {
                "host": "sftp.example.com",
                "port": 22,
                "user": "sftpuser",
                "password": "sftppass"
            },
            "max_concurrent_transfers": 3,
            "is_active": True
        }
        
        print("\nCreating SFTP endpoint...")
        response = await client.post(f"{BASE_URL}/endpoints/", json=sftp_endpoint)
        if response.status_code == 200:
            print("✅ SFTP endpoint created successfully")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Failed to create SFTP endpoint: {response.status_code}")
            print(f"   Error: {response.text}")
        
        # List all endpoints
        print("\nListing all endpoints...")
        response = await client.get(f"{BASE_URL}/endpoints/")
        if response.status_code == 200:
            endpoints = response.json()
            print(f"✅ Found {len(endpoints)} endpoints:")
            for ep in endpoints:
                print(f"   - {ep['name']} ({ep['type']})")
        else:
            print(f"❌ Failed to list endpoints: {response.status_code}")

async def test_endpoint_connection():
    """Test endpoint connections"""
    async with httpx.AsyncClient() as client:
        # Get endpoints
        response = await client.get(f"{BASE_URL}/endpoints/")
        endpoints = response.json()
        
        # Find our test endpoints
        smb_ep = next((ep for ep in endpoints if ep['name'] == "Test SMB Share"), None)
        sftp_ep = next((ep for ep in endpoints if ep['name'] == "Test SFTP Server"), None)
        
        if smb_ep:
            print("\nTesting SMB endpoint connection...")
            response = await client.post(f"{BASE_URL}/endpoints/{smb_ep['id']}/test")
            print(f"   Status: {response.status_code}")
            print(f"   Result: {response.json()}")
        
        if sftp_ep:
            print("\nTesting SFTP endpoint connection...")
            response = await client.post(f"{BASE_URL}/endpoints/{sftp_ep['id']}/test")
            print(f"   Status: {response.status_code}")
            print(f"   Result: {response.json()}")

async def main():
    print("SMB/SFTP Endpoint API Test")
    print("=" * 50)
    
    await create_test_endpoints()
    await test_endpoint_connection()
    
    print("\n" + "=" * 50)
    print("✅ Test complete!")
    print("\nYou can now:")
    print("1. Check the endpoints in the UI at http://localhost:3000")
    print("2. Create a transfer using these endpoints")
    print("3. Update the connection details to real servers for actual testing")

if __name__ == "__main__":
    asyncio.run(main())