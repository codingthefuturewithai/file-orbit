# SMB/SFTP Configuration Guide

## Overview
This guide explains how to configure and use SMB/CIFS and SFTP endpoints in File Orbit.

## SMB/CIFS Configuration

### Required Fields
- **Host**: The IP address or hostname of the SMB server (e.g., `192.168.1.100` or `fileserver.local`)
- **User**: Username for authentication
- **Password**: Password for authentication
- **Domain**: Windows domain (default: `WORKGROUP`)

### Path Format
For SMB endpoints, paths should include the share name:
- `share-name/folder/subfolder`
- `videos/2024/june/`
- `backup/archive/`

### Example Configuration
```json
{
  "host": "192.168.1.100",
  "user": "fileuser",
  "password": "secretpassword",
  "domain": "COMPANY"
}
```

### Common Issues
1. **Access Denied**: Verify credentials and share permissions
2. **Host Not Found**: Check network connectivity and hostname resolution
3. **Share Not Found**: Ensure the share name is included in the path

## SFTP Configuration

### Authentication Methods

#### Password Authentication
```json
{
  "host": "sftp.example.com",
  "port": 22,
  "user": "sftpuser",
  "password": "secretpassword"
}
```

#### SSH Key Authentication
```json
{
  "host": "sftp.example.com",
  "port": 22,
  "user": "sftpuser",
  "key_file": "/home/user/.ssh/id_rsa",
  "key_passphrase": "optional-passphrase"
}
```

### Path Format
- **Absolute paths**: Start with `/` (e.g., `/home/user/files/`)
- **Relative paths**: Relative to user's home directory (e.g., `files/uploads/`)

### Security Options
- **known_hosts_file**: Path to SSH known hosts file for server verification

### Common Issues
1. **Connection Refused**: Check firewall rules and SSH service status
2. **Authentication Failed**: Verify credentials or SSH key permissions
3. **Permission Denied**: Check file/directory permissions on the server

## Testing Endpoints

### Using the UI
1. Navigate to the Endpoints section
2. Click "Add Endpoint"
3. Select SMB or SFTP as the type
4. Fill in the configuration fields
5. Click "Test Connection" to verify

### Using the Test Script
```bash
cd backend
python test_remote_endpoints.py
```

Update the script with your actual connection details before running.

## Transfer Examples

### SMB Transfer
- **Source**: Local directory `/tmp/videos/`
- **Destination**: SMB share `videos/2024/processed/`
- **Result**: Files uploaded to `\\fileserver\videos\2024\processed\`

### SFTP Transfer
- **Source**: S3 bucket `s3://mybucket/incoming/`
- **Destination**: SFTP path `/var/www/media/`
- **Result**: Files uploaded via SFTP to remote server

## Security Best Practices

1. **Use Strong Passwords**: Avoid default or weak passwords
2. **SSH Keys**: Prefer SSH key authentication over passwords for SFTP
3. **Restrict Permissions**: Use accounts with minimal required permissions
4. **Secure Storage**: In production, use encrypted credential storage
5. **Network Security**: Use VPN or secure networks for SMB transfers

## Troubleshooting

### Enable Debug Logging
Add to worker.py for detailed rclone output:
```python
logging.getLogger("app.services.rclone_service").setLevel(logging.DEBUG)
```

### Test with rclone CLI
```bash
# Test SMB
rclone lsd :smb:share-name --smb-host=192.168.1.100 --smb-user=myuser --smb-pass=mypass

# Test SFTP
rclone lsd :sftp:/ --sftp-host=sftp.example.com --sftp-user=myuser --sftp-pass=mypass
```

### Check Logs
View transfer logs in the UI under the Logs section or check:
- `/tmp/file-orbit/logs/transfers.log`
- `/tmp/file-orbit/logs/system.log`