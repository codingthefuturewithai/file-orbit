# CTF Rclone MVP Features

## Reality Check: What Actually Works

### ✅ Working Features (Local Only)
- **Local directory → Local directory transfers**
- **File watching on local directories**
- **Manual transfer creation via UI**
- **Transfer history and monitoring**
- **Basic job queue processing**
- **Endpoint CRUD operations** - Full create, read, update, delete functionality
- **Enhanced error handling** - Detailed validation messages in UI
- **Bandwidth configuration** - Support for human-readable formats (10M, 1G, etc.)

### ❌ Not Working (Required for Production)
- **S3 transfers** - Code exists, just needs AWS credentials in .env (30 min fix)
- **SMB/CIFS transfers** - UI exists but rclone config NOT IMPLEMENTED (3 hours to implement)
- **SFTP transfers** - UI exists but rclone config NOT IMPLEMENTED (3 hours to implement)
- **S3 event monitoring** - SQS integration not configured
- **Cross-machine transfers** - Only local paths work
- **Network error handling** - No retry logic
- **Credential security** - Stored in plain text
- **Log Viewer UI** - Cannot view logs without SSH access (3 hours to implement)
- **DISTRIBUTED ARCHITECTURE** - Cannot control transfers between remote servers
  - Current: UI on Server A can only transfer files on Server A
  - Required: UI on Server A controls transfers from Server B to Server C
  - See [DISTRIBUTED_ARCHITECTURE.md](DISTRIBUTED_ARCHITECTURE.md)

## Current Feature Status

### ✅ Fully Implemented Features (Local Only)

#### 1. Manual File Transfers
- Create one-time transfers between endpoints via web UI
- Support for multiple endpoint types (Local, S3, SMB/CIFS, SFTP)
- Real-time progress monitoring
- Transfer history with filtering and pagination
- Retry failed transfers
- Cancel running transfers

#### 2. Endpoint Management
- **Create** new endpoints with configuration
- **Edit** existing endpoint settings
- **Delete** endpoints (with cascade handling)
- **Configure throttling** per endpoint (concurrent transfer limits)
- **Test connection** before saving
- Supported types:
  - Local file system
  - S3 (bucket configuration ready, needs AWS credentials)
  - SMB/CIFS (configuration ready, needs network access)
  - SFTP (configuration ready, needs SSH access)

#### 3. Transfer Templates Management
- Create templates for automated transfers
- Configure file patterns (e.g., *.mp4, *.mxf)
- Set up destination path templates with variables
- Chain transfers (file moves through multiple destinations)
- Enable/disable templates
- Full CRUD operations via UI

#### 4. Event-Driven Transfers (Local Only)
- **File system monitoring** using watchdog library
- Automatic transfer triggering when files appear
- Pattern matching for selective transfers
- Path templating with variables:
  - `{year}`, `{month}`, `{day}`
  - `{filename}`, `{basename}`, `{extension}`
- Transfer chains (e.g., Source → Primary → Archive)

#### 5. Dashboard & Monitoring
- Real-time statistics:
  - Active transfers count
  - Completed transfers count
  - Failed transfers count
- 10 most recent transfers display
- Job details modal with comprehensive information:
  - Source/destination paths
  - Transfer progress
  - Error messages
  - Timing information

#### 6. Transfer History
- Comprehensive transfer log
- Advanced filtering:
  - By status (completed, failed, running)
  - By type (manual, scheduled, event-driven)
  - By date range
  - Text search
- Pagination (10, 25, 50, 100 items per page)
- Detailed job information modal

#### 7. Safe File Writing (Temporary Files)
- **Atomic file transfers** using rclone's default behavior
- Files upload with `.partial` suffix during transfer
- Automatic rename to final filename only after successful completion
- Prevents partial files from being read by downstream systems
- Configurable temporary directory per endpoint
- Custom partial file suffix support

#### 8. Checksum Verification
- **Data integrity validation** after transfers
- Uses rclone's `--checksum` flag for hash-based verification
- Compares source and destination file hashes
- Optional per-transfer configuration
- Supports multiple hash algorithms (MD5, SHA1, etc.)
- Checksum mismatch detection and error reporting

#### 9. Log Viewer (NEW - June 29, 2025)
- **System log viewing** without SSH access
- Support for backend, worker, event-monitor, and scheduler logs
- Real-time log filtering and search
- Adjustable line count (50, 100, 500, 1000)
- Auto-refresh functionality (5-second intervals)
- Syntax highlighting for log levels (ERROR, WARNING, INFO, DEBUG)
- Dark theme for better readability

### 🟡 Partially Implemented Features

#### 1. Scheduled Transfers
- ✅ Create scheduled jobs with cron expressions
- ✅ Cron expression validation
- ✅ Schedule display in UI
- ❌ Automatic execution (scheduler service exists but not integrated)

#### 2. S3 Integration
- ✅ S3 endpoint configuration UI
- ✅ S3 event monitor code structure
- ❌ AWS credentials configuration
- ❌ Actual S3 bucket monitoring
- ❌ S3-to-local transfers

### ❌ Not Implemented Features

#### 1. Authentication & Authorization
- No login system
- No user management
- No role-based access control
- No audit trail of user actions

#### 2. Real Cloud Storage Integration
- S3 buckets (code exists, not configured)
- SMB/CIFS shares (UI exists, not tested)
- SFTP servers (UI exists, not tested)

#### 3. Advanced Monitoring
- Prometheus metrics export
- Grafana dashboards
- Performance analytics
- Bandwidth utilization graphs

#### 4. Notifications
- Email alerts on failure
- Webhook integration
- Slack/Teams notifications

#### 5. Disk Space Management
- Pre-transfer space checking (not reliable across all backends)
- Automatic pause when disk space threshold reached
- Space-based transfer queuing
- Note: Rclone limitation - `about` command unsupported on SMB/CIFS/local

## Testing Current Features

### Test Manual Transfers
1. Start all services: `./manage.sh start`
2. Open http://localhost:3000
3. Go to "Endpoints" and create source/destination
4. Click "Create Transfer"
5. Select endpoints and paths
6. Click "Create & Execute"
7. Monitor progress on dashboard

### Test Event-Driven Transfers
1. Ensure event monitor is running: `./manage.sh status`
2. Create a transfer template in the UI
3. Drop a file in the watched directory:
   ```bash
   cp test-file.mp4 /tmp/ctf-rclone-test/watch/
   ```
4. Check dashboard for automatic transfer

### Test Endpoint Management
1. Go to "Endpoints" page
2. Click "Add Endpoint"
3. Configure endpoint settings
4. Set concurrent transfer limit
5. Save and verify in list

### Test Transfer Templates
1. Go to "Transfer Templates" page
2. Create template with:
   - Watch path: `/tmp/ctf-rclone-test/watch`
   - File pattern: `*.mp4`
   - Destination template: `/archive/{year}/{month}/{filename}`
3. Test with file drop

## Configuration Examples

### Local Endpoint
```json
{
  "type": "local",
  "config": {
    "path": "/tmp/ctf-rclone-test/source"
  }
}
```

### S3 Endpoint (Ready but needs credentials)
```json
{
  "type": "s3",
  "config": {
    "provider": "AWS",
    "access_key_id": "YOUR_KEY",
    "secret_access_key": "YOUR_SECRET",
    "region": "us-east-1",
    "bucket": "your-bucket"
  }
}
```

### Transfer Template Example
```json
{
  "name": "Archive MP4 Files",
  "event_type": "FILE_CREATED",
  "source_endpoint_id": "local-watch",
  "destination_endpoint_id": "archive-storage",
  "file_pattern": "*.mp4",
  "destination_path_template": "/archive/{year}/{month}/{day}/{filename}",
  "is_active": true
}
```

## Limitations

1. **All transfers are currently LOCAL only** - no real cloud storage
2. **No authentication** - anyone can access the UI
3. **S3 events not working** - only local file system events
4. **Scheduler not running automatically** - jobs created but not executed
5. **No email notifications** - code structure exists but not configured
6. **No disk space threshold monitoring** - Cannot reliably check remote storage space
   - Rclone's `about` command not supported on SMB/CIFS and local filesystems
   - No automatic pause/resume based on available space
   - Transfers will fail when disk is full (handle via error recovery)