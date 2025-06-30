#!/usr/bin/env python3
"""
Test script for SMB and SFTP endpoint configurations
"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.services.rclone_service import RcloneService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_smb_endpoint():
    """Test SMB endpoint configuration"""
    print("\n=== Testing SMB Endpoint ===")
    
    rclone = RcloneService()
    
    # Example SMB configuration
    smb_config = {
        'type': 'smb',
        'host': '192.168.1.100',  # Replace with your SMB server
        'user': 'myuser',         # Replace with your username
        'pass': 'mypassword',     # Replace with your password
        'domain': 'WORKGROUP'     # Replace with your domain if needed
    }
    
    print(f"Testing SMB connection to {smb_config['host']}...")
    
    try:
        # Test connection
        connected = await rclone.test_remote_connection("smb_test", smb_config)
        print(f"Connection test: {'SUCCESS' if connected else 'FAILED'}")
        
        if connected:
            # Try to list files in a share
            await rclone.configure_remote("smb_test", smb_config)
            files = await rclone.list_files("smb_test", "share_name/path", "*")
            print(f"Found {len(files)} files")
            for f in files[:5]:  # Show first 5 files
                print(f"  - {f['name']} ({f['size']} bytes)")
    
    except Exception as e:
        print(f"Error: {e}")
        
async def test_sftp_endpoint():
    """Test SFTP endpoint configuration"""
    print("\n=== Testing SFTP Endpoint ===")
    
    rclone = RcloneService()
    
    # Example SFTP configuration with password
    sftp_config_password = {
        'type': 'sftp',
        'host': 'sftp.example.com',  # Replace with your SFTP server
        'user': 'myuser',            # Replace with your username
        'pass': 'mypassword',        # Replace with your password
        'port': 22
    }
    
    # Example SFTP configuration with SSH key
    sftp_config_key = {
        'type': 'sftp',
        'host': 'sftp.example.com',              # Replace with your SFTP server
        'user': 'myuser',                        # Replace with your username
        'key_file': '/home/user/.ssh/id_rsa',   # Replace with your key path
        'port': 22
    }
    
    print(f"Testing SFTP connection to {sftp_config_password['host']}...")
    
    try:
        # Test password authentication
        connected = await rclone.test_remote_connection("sftp_test", sftp_config_password)
        print(f"Password auth test: {'SUCCESS' if connected else 'FAILED'}")
        
        if connected:
            # Try to list files in home directory
            await rclone.configure_remote("sftp_test", sftp_config_password)
            files = await rclone.list_files("sftp_test", ".", "*")
            print(f"Found {len(files)} files in home directory")
            for f in files[:5]:  # Show first 5 files
                print(f"  - {f['name']} ({f['size']} bytes)")
    
    except Exception as e:
        print(f"Error: {e}")

async def test_local_to_smb_transfer():
    """Test transferring files from local to SMB"""
    print("\n=== Testing Local to SMB Transfer ===")
    
    rclone = RcloneService()
    
    # Configure local source
    local_config = {
        'type': 'local',
        'path': '/tmp/file-orbit/source'
    }
    
    # Configure SMB destination
    smb_config = {
        'type': 'smb',
        'host': '192.168.1.100',
        'user': 'myuser',
        'pass': 'mypassword',
        'domain': 'WORKGROUP'
    }
    
    try:
        await rclone.configure_remote("source", local_config)
        await rclone.configure_remote("dest", smb_config)
        
        # Start transfer
        source_path = rclone._build_path("source", "/tmp/file-orbit/source/*.mp4")
        dest_path = rclone._build_path("dest", "share_name/videos/")
        
        print(f"Transferring from {source_path} to {dest_path}")
        
        process = await rclone.start_transfer(source_path, dest_path)
        
        # Wait for completion
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            print("Transfer completed successfully!")
        else:
            print(f"Transfer failed: {stderr.decode()}")
            
    except Exception as e:
        print(f"Error: {e}")

async def main():
    """Run all tests"""
    print("Remote Endpoint Test Suite")
    print("=" * 50)
    print("\nNOTE: Update the connection details in this script before running!")
    print("Replace example hostnames, usernames, and passwords with real values.")
    print("\nUncomment the tests you want to run:")
    
    # Uncomment the tests you want to run:
    # await test_smb_endpoint()
    # await test_sftp_endpoint()
    # await test_local_to_smb_transfer()
    
    print("\nTo test endpoints through the UI:")
    print("1. Start the services: ./manage.sh start all")
    print("2. Navigate to http://localhost:3000")
    print("3. Go to Endpoints section")
    print("4. Create new SMB or SFTP endpoint")
    print("5. Use 'Test Connection' button to verify")

if __name__ == "__main__":
    asyncio.run(main())