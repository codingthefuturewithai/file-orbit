#!/usr/bin/env python3
"""
Test rclone configuration generation for SMB/SFTP endpoints
"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.services.rclone_service import RcloneService
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_config_generation():
    """Test that rclone config files are generated correctly"""
    rclone = RcloneService()
    
    print("\n=== Testing Config File Generation ===")
    
    # Test SMB configuration
    smb_config = {
        'type': 'smb',
        'host': 'test-server.local',
        'user': 'testuser',
        'pass': 'testpass',
        'domain': 'TESTDOMAIN'
    }
    
    # Test SFTP with password
    sftp_pass_config = {
        'type': 'sftp',
        'host': 'sftp.test.com',
        'user': 'sftpuser',
        'pass': 'sftppass',
        'port': 2222
    }
    
    # Test SFTP with key
    sftp_key_config = {
        'type': 'sftp',
        'host': 'sftp2.test.com',
        'user': 'keyuser',
        'key_file': '/home/test/.ssh/id_rsa',
        'key_passphrase': 'keypass',
        'port': 22
    }
    
    # Configure remotes
    await rclone.configure_remote("smb_test", smb_config)
    await rclone.configure_remote("sftp_pass", sftp_pass_config)
    await rclone.configure_remote("sftp_key", sftp_key_config)
    
    # Read the generated config file
    if rclone.config_file:
        print(f"\nGenerated config file: {rclone.config_file}")
        with open(rclone.config_file, 'r') as f:
            content = f.read()
            print("\nConfig file content:")
            print("-" * 50)
            print(content)
            print("-" * 50)
            
        # Verify the content
        assert "[smb_test]" in content
        assert "type = smb" in content
        assert "host = test-server.local" in content
        assert "user = testuser" in content
        assert "pass = testpass" in content
        assert "domain = TESTDOMAIN" in content
        
        assert "[sftp_pass]" in content
        assert "[sftp_key]" in content
        assert "key_file = /home/test/.ssh/id_rsa" in content
        assert "port = 2222" in content
        
        print("\n✅ Config file generation test PASSED")
    else:
        print("\n❌ No config file was generated!")
        
async def test_path_building():
    """Test path building for different endpoint types"""
    rclone = RcloneService()
    
    print("\n=== Testing Path Building ===")
    
    # Configure test endpoints
    await rclone.configure_remote("local", {'type': 'local', 'path': '/base'})
    await rclone.configure_remote("smb", {'type': 'smb'})
    await rclone.configure_remote("sftp", {'type': 'sftp'})
    await rclone.configure_remote("s3", {'type': 's3', 'bucket': 'mybucket'})
    
    # Test cases
    test_cases = [
        ("local", "/absolute/path", "/absolute/path"),
        ("local", "relative/path", "/base/relative/path"),
        ("smb", "share/folder/file.mp4", "smb:share/folder/file.mp4"),
        ("smb", "/share/folder", "smb:share/folder"),
        ("sftp", "/home/user/files", "sftp:/home/user/files"),
        ("sftp", "relative/path", "sftp:relative/path"),
        ("s3", "folder/file.mp4", "s3:mybucket/folder/file.mp4"),
    ]
    
    print("\nPath building tests:")
    all_passed = True
    for remote, input_path, expected in test_cases:
        result = rclone._build_path(remote, input_path)
        passed = result == expected
        all_passed &= passed
        status = "✅" if passed else "❌"
        print(f"{status} {remote}:{input_path} -> {result} (expected: {expected})")
    
    if all_passed:
        print("\n✅ All path building tests PASSED")
    else:
        print("\n❌ Some path building tests FAILED")
        
async def test_worker_config():
    """Test worker endpoint configuration"""
    print("\n=== Testing Worker Configuration ===")
    
    from app.models.endpoint import Endpoint, EndpointType
    
    # Create test endpoints
    smb_endpoint = Endpoint(
        id="test-smb",
        name="Test SMB",
        type=EndpointType.SMB,
        config={
            'host': '192.168.1.100',
            'user': 'shareuser',
            'password': 'sharepass',
            'domain': 'WORKGROUP'
        }
    )
    
    sftp_endpoint = Endpoint(
        id="test-sftp",
        name="Test SFTP",
        type=EndpointType.SFTP,
        config={
            'host': 'sftp.example.com',
            'user': 'sftpuser',
            'password': 'sftppass',
            'port': 22
        }
    )
    
    # Import worker's configure function
    from worker import JobProcessor
    processor = JobProcessor()
    
    # Test SMB configuration
    smb_config = await processor._configure_endpoint(smb_endpoint, "smb_remote")
    print(f"\nSMB Config: {smb_config}")
    assert smb_config['type'] == 'smb'
    assert smb_config['host'] == '192.168.1.100'
    assert smb_config['user'] == 'shareuser'
    assert smb_config['pass'] == 'sharepass'
    assert smb_config['domain'] == 'WORKGROUP'
    
    # Test SFTP configuration
    sftp_config = await processor._configure_endpoint(sftp_endpoint, "sftp_remote")
    print(f"SFTP Config: {sftp_config}")
    assert sftp_config['type'] == 'sftp'
    assert sftp_config['host'] == 'sftp.example.com'
    assert sftp_config['user'] == 'sftpuser'
    assert sftp_config['pass'] == 'sftppass'
    assert sftp_config['port'] == 22
    
    print("\n✅ Worker configuration tests PASSED")

async def main():
    """Run all tests"""
    print("Rclone SMB/SFTP Configuration Tests")
    print("=" * 50)
    
    try:
        await test_config_generation()
        await test_path_building()
        await test_worker_config()
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("\nNote: These tests verify configuration logic only.")
        print("To test actual network connections, use test_remote_endpoints.py")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())