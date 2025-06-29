# Remote Transfer Quick Start Guide

## Current State
- ✅ Local directory transfers work
- ❌ S3 transfers not configured
- ❌ SMB transfers not tested
- ❌ SFTP transfers not tested

## Step 1: Enable S3 Transfers (30 minutes)

### 1.1 Add AWS Credentials
```bash
# Add to mvp/backend/.env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
```

### 1.2 Update S3 Endpoint Configuration
```python
# File: mvp/backend/app/services/rclone_service.py
# Update _configure_endpoint method for S3

elif endpoint.type == 's3':
    config.update({
        'type': 's3',
        'provider': 'AWS',
        'access_key_id': endpoint.config.get('access_key'),
        'secret_access_key': endpoint.config.get('secret_key'),
        'region': endpoint.config.get('region', 'us-east-1'),
        'env_auth': False  # Use explicit credentials
    })
```

### 1.3 Test S3 Connection
```python
# Add to mvp/backend/test_s3_transfer.py
import asyncio
from app.services.rclone_service import RcloneService

async def test_s3():
    rclone = RcloneService()
    
    # Configure S3 remote
    await rclone.configure_remote('s3test', {
        'type': 's3',
        'provider': 'AWS',
        'access_key_id': 'YOUR_KEY',
        'secret_access_key': 'YOUR_SECRET',
        'region': 'us-east-1'
    })
    
    # List files
    files = await rclone.list_files('s3test', 'your-bucket/path')
    print(f"Found {len(files)} files")

asyncio.run(test_s3())
```

## Step 2: Enable SMB/CIFS Transfers (1 hour)

### 2.1 Install SMB Dependencies
```bash
# macOS
brew install samba

# Linux
sudo apt-get install cifs-utils
```

### 2.2 Update SMB Configuration
```python
# File: mvp/backend/app/services/rclone_service.py

elif endpoint.type == 'smb':
    config.update({
        'type': 'smb',
        'host': endpoint.config.get('host'),
        'user': endpoint.config.get('username'),
        'pass': endpoint.config.get('password'),
        'domain': endpoint.config.get('domain', 'WORKGROUP'),
        'port': endpoint.config.get('port', 445)
    })
```

### 2.3 Test SMB Connection
```bash
# Test mount manually first
mkdir -p /tmp/smbtest
mount -t smbfs //user:pass@server/share /tmp/smbtest

# Or with rclone
rclone lsd smb: --smb-host=server --smb-user=user --smb-pass=pass
```

## Step 3: Enable SFTP Transfers (30 minutes)

### 3.1 Update SFTP Configuration
```python
# File: mvp/backend/app/services/rclone_service.py

elif endpoint.type == 'sftp':
    config.update({
        'type': 'sftp',
        'host': endpoint.config.get('host'),
        'user': endpoint.config.get('username'),
        'port': endpoint.config.get('port', 22),
        'pass': endpoint.config.get('password'),
        'key_file': endpoint.config.get('key_file'),
        'key_use_agent': False
    })
```

### 3.2 Test SFTP Connection
```bash
# Test with rclone directly
rclone lsd sftp: --sftp-host=server --sftp-user=user --sftp-pass=pass
```

## Step 4: Add Endpoint Testing API (1 hour)

### 4.1 Create Test Endpoint
```python
# File: mvp/backend/app/api/api_v1/endpoints/endpoints.py

@router.post("/{endpoint_id}/test")
async def test_endpoint_connection(
    endpoint_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Test endpoint connectivity"""
    endpoint = await get_endpoint(db, endpoint_id)
    if not endpoint:
        raise HTTPException(404, "Endpoint not found")
    
    rclone = RcloneService()
    
    try:
        # Configure the endpoint
        await rclone.configure_remote("test", endpoint.config)
        
        # Try to list files
        files = await rclone.list_files("test", "/")
        
        return {
            "status": "connected",
            "message": f"Successfully connected. Found {len(files)} items.",
            "can_read": True,
            "can_write": True  # Would need actual write test
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": str(e),
            "can_read": False,
            "can_write": False
        }
```

### 4.2 Add UI Test Button
```typescript
// File: mvp/frontend/src/pages/Endpoints.tsx

const testConnection = async (endpointId: string) => {
  try {
    const response = await api.post(`/endpoints/${endpointId}/test`);
    if (response.data.status === 'connected') {
      alert('Connection successful!');
    } else {
      alert(`Connection failed: ${response.data.message}`);
    }
  } catch (error) {
    alert('Failed to test connection');
  }
};
```

## Step 5: Quick S3 Event Integration (2 hours)

### 5.1 Add SQS Configuration
```python
# File: mvp/backend/app/core/config.py

AWS_SQS_QUEUE_URL = os.getenv("AWS_SQS_QUEUE_URL")
AWS_SQS_POLL_INTERVAL = int(os.getenv("AWS_SQS_POLL_INTERVAL", "10"))
```

### 5.2 Create SQS Polling Service
```python
# File: mvp/backend/app/services/sqs_monitor.py

import boto3
import json
import asyncio
from app.services.redis_manager import redis_manager

class SQSMonitor:
    def __init__(self):
        self.sqs = boto3.client('sqs')
        self.queue_url = settings.AWS_SQS_QUEUE_URL
        
    async def poll_messages(self):
        """Poll SQS for S3 events"""
        while True:
            try:
                response = self.sqs.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20  # Long polling
                )
                
                messages = response.get('Messages', [])
                for message in messages:
                    await self.process_s3_event(message)
                    
                    # Delete processed message
                    self.sqs.delete_message(
                        QueueUrl=self.queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    
            except Exception as e:
                logger.error(f"SQS polling error: {e}")
                
            await asyncio.sleep(1)
    
    async def process_s3_event(self, message):
        """Process S3 event from SQS"""
        body = json.loads(message['Body'])
        
        # Parse S3 event
        for record in body.get('Records', []):
            if record['eventName'].startswith('s3:ObjectCreated'):
                bucket = record['s3']['bucket']['name']
                key = record['s3']['object']['key']
                
                # Find matching transfer template
                # Create job
                # Queue for processing
```

## Testing Remote Transfers

### Test S3 to Local
```bash
# Create test endpoint via API
curl -X POST localhost:8000/api/v1/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test S3 Bucket",
    "type": "s3",
    "config": {
      "access_key": "YOUR_KEY",
      "secret_key": "YOUR_SECRET",
      "region": "us-east-1",
      "bucket": "test-bucket"
    }
  }'

# Create manual transfer
curl -X POST localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_endpoint_id": "s3-endpoint-id",
    "source_path": "/test-bucket/input/",
    "destination_endpoint_id": "local-endpoint-id",
    "destination_path": "/tmp/output/"
  }'
```

### Test SMB to S3
```bash
# Similar process but with SMB source and S3 destination
```

## Common Issues

### S3 Access Denied
- Check IAM permissions for bucket
- Verify credentials are correct
- Check bucket policy allows access

### SMB Connection Failed
- Verify network connectivity
- Check firewall rules (port 445)
- Try with domain\username format
- Verify SMB version compatibility

### SFTP Key Issues
- Convert PuTTY keys to OpenSSH format
- Set correct permissions (600) on key file
- Try password auth first

## Next Steps

1. **Today**: Get S3 transfers working
2. **Tomorrow**: Test SMB transfers
3. **This Week**: Implement S3 event monitoring
4. **Next Week**: Production hardening