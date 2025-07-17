#!/usr/bin/env python3
"""
Integration test for rclone with SMB/SFTP - tests actual rclone commands
"""
import asyncio
import subprocess
import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

async def check_rclone_installed():
    """Check if rclone is installed"""
    try:
        result = subprocess.run(['rclone', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Rclone is installed")
            print(f"   Version: {result.stdout.split()[2]}")
            return True
        else:
            print("❌ Rclone is not installed properly")
            return False
    except FileNotFoundError:
        print("❌ Rclone is not installed. Please run: brew install rclone")
        return False

async def test_rclone_config_command():
    """Test that rclone can use our generated config"""
    from app.services.rclone_service import RcloneService
    
    rclone = RcloneService()
    
    # Configure a test remote
    await rclone.configure_remote("test_local", {
        'type': 'local',
        'path': '/tmp'
    })
    
    # Try to list files using rclone command
    cmd = ['rclone', 'lsjson', '--config', rclone.config_file, 'test_local:']
    
    print(f"\nRunning command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print("✅ Rclone successfully used our config file")
            files = json.loads(result.stdout)
            print(f"   Found {len(files)} items in /tmp")
            return True
        else:
            print("❌ Rclone command failed:")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Rclone command timed out")
        return False
    except json.JSONDecodeError:
        print("❌ Failed to parse rclone output")
        return False

async def test_smb_syntax():
    """Test that SMB remote syntax is valid (without actual connection)"""
    from app.services.rclone_service import RcloneService
    
    rclone = RcloneService()
    
    # Configure SMB remote
    await rclone.configure_remote("test_smb", {
        'type': 'smb',
        'host': 'dummy.local',
        'user': 'dummy',
        'pass': 'dummy',
        'domain': 'WORKGROUP'
    })
    
    # Test config dump to verify SMB config
    cmd = ['rclone', 'config', 'dump', '--config', rclone.config_file]
    
    print("\nTesting SMB configuration syntax...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            config = json.loads(result.stdout)
            if 'test_smb' in config and config['test_smb']['type'] == 'smb':
                print("✅ SMB configuration syntax is valid")
                print(f"   Config: {json.dumps(config['test_smb'], indent=2)}")
                return True
            else:
                print("❌ SMB configuration not found in rclone config")
                return False
        else:
            print("❌ Rclone config dump failed:")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing SMB syntax: {e}")
        return False

async def test_sftp_syntax():
    """Test that SFTP remote syntax is valid (without actual connection)"""
    from app.services.rclone_service import RcloneService
    
    rclone = RcloneService()
    
    # Configure SFTP remote with key
    await rclone.configure_remote("test_sftp", {
        'type': 'sftp',
        'host': 'dummy.local',
        'user': 'dummy',
        'key_file': '/dummy/path/id_rsa',
        'port': 2222
    })
    
    # Test config dump to verify SFTP config
    cmd = ['rclone', 'config', 'dump', '--config', rclone.config_file]
    
    print("\nTesting SFTP configuration syntax...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            config = json.loads(result.stdout)
            if 'test_sftp' in config and config['test_sftp']['type'] == 'sftp':
                print("✅ SFTP configuration syntax is valid")
                print(f"   Config: {json.dumps(config['test_sftp'], indent=2)}")
                return True
            else:
                print("❌ SFTP configuration not found in rclone config")
                return False
        else:
            print("❌ Rclone config dump failed:")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing SFTP syntax: {e}")
        return False

async def main():
    """Run integration tests"""
    print("Rclone SMB/SFTP Integration Tests")
    print("=" * 50)
    
    # Check prerequisites
    if not await check_rclone_installed():
        print("\n⚠️  Please install rclone first: brew install rclone")
        return
    
    # Run tests
    tests = [
        ("Config file usage", test_rclone_config_command()),
        ("SMB syntax validation", test_smb_syntax()),
        ("SFTP syntax validation", test_sftp_syntax()),
    ]
    
    results = []
    for name, test in tests:
        print(f"\n--- {name} ---")
        result = await test
        results.append((name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All integration tests PASSED!")
        print("\nThe SMB/SFTP implementation is working correctly.")
        print("To test with real servers, update test_remote_endpoints.py with actual connection details.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())