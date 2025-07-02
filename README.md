# File Orbit

Enterprise file transfer orchestration system built on top of rclone for automated, reliable file transfers between cloud storage, network shares, and local systems.

## 🚀 Getting Started

**[Follow the Setup Guide](docs/SETUP_GUIDE.md)** for installation and configuration instructions.

## What File Orbit Does Today

File Orbit provides a web-based interface for managing file transfers with these current capabilities:

- **Automated Transfers**: Trigger transfers when files appear in watched directories
- **Manual Transfers**: Create and monitor one-time transfers through the web UI
- **Multiple Storage Types**: Connect S3 buckets, SMB/CIFS shares, SFTP servers, and local directories
- **Progress Monitoring**: Track transfer status and completion in real-time
- **Concurrent Transfer Limits**: Control how many jobs run simultaneously per endpoint (job-level throttling)
- **Transfer History**: Search and filter all past transfers with retry capabilities
- **Path Templates**: Use dynamic variables like {year}, {month}, {filename} in destination paths

## Coming Soon

These features are implemented but need final integration:
- **Scheduled Transfers**: Cron-based scheduling (code complete, not auto-enabled)
- **S3 Event Triggers**: Respond to S3 bucket events via SQS (requires AWS setup)
- **Bandwidth Throttling**: Per-endpoint bandwidth limits (UI ready, needs backend integration)
- **Email Notifications**: Transfer completion alerts (structure in place)
- **File-Level Throttling**: Current throttling works at job level; file-level throttling planned

## Important Limitations

### Concurrent Transfer Throttling
Currently, throttling works at the **job level**, not the file level. This means:
- If an endpoint has a 5 concurrent transfer limit, it limits to 5 concurrent **jobs**
- Each job may contain multiple files that transfer sequentially
- A job with 100 files counts as 1 concurrent transfer, not 100
- The throttle check happens when the job starts but slots are not properly acquired/released

**Example**: With a 5 concurrent transfer limit on an endpoint:
- 5 jobs with 10 files each = 5 concurrent jobs (50 files transferring in 5 parallel streams)
- The system won't limit individual files within those jobs

We plan to implement proper file-level throttling in a future release.


## 📸 Screenshots

### Dashboard
![Dashboard](docs/images/dashboard.png)
The main dashboard provides an at-a-glance view of your file transfer operations, including:
- Real-time statistics (total transfers, active transfers, failed transfers, success rate)
- Active transfers with live progress bars
- Recent transfer history

### Configure Endpoints
![Configure Endpoints](docs/images/configure_endpoints.png)
Manage your storage endpoints with support for:
- Multiple storage types (Local, S3, SMB/CIFS, SFTP)
- Concurrent transfer limits per endpoint
- Bandwidth throttling
- Easy configuration and testing

### Create Transfer
![Create Transfer](docs/images/create_transfer.png)
Create manual file transfers with:
- Source and destination endpoint selection
- Path browsing and selection
- File pattern filtering (e.g., *.mp4, *.mov)
- Schedule configuration for recurring transfers
- Path template variables ({year}, {month}, {day}, {filename})

### Transfer Templates
![Create Transfer Template](docs/images/create_transfer_template.png)
Define automated transfer workflows that trigger based on:
- S3 events (object created)
- File system events (file created/modified)
- Manual triggers
- Support for destination path templates with variable substitution

### Transfer History
![Transfer History](docs/images/transfer_history.png)
Track all transfers with:
- Comprehensive filtering by status, type, date range
- Search functionality
- Detailed transfer information
- Retry capabilities for failed transfers

### System Logs
![System Logs](docs/images/system_logs.png)
Monitor system operations with:
- Real-time log viewing for all services (backend, worker, event monitor)
- Log filtering and search
- Auto-refresh capabilities
- Service-specific log selection

## Documentation

- 📐 [Architecture Overview](docs/ARCHITECTURE.md) - System design and components
- 🚀 [Running Services](docs/RUNNING_SERVICES.md) - How to start, stop, and manage services  
- ✨ [Features Guide](docs/FEATURES.md) - Current capabilities and limitations
- 🛠️ [Setup Guide](docs/SETUP_GUIDE.md) - Detailed installation instructions

## Project Structure
```
file-orbit/
├── manage.sh         # Service management script
├── backend/          # FastAPI backend
│   ├── app/         # Application code
│   ├── worker.py    # Job processor
│   ├── event_monitor_service.py  # File watcher
│   └── scheduler_service.py      # Cron scheduler
├── frontend/        # React frontend
│   └── src/        # React components
├── docker-compose.yml  # Infrastructure services
├── docs/           # Documentation
└── logs/           # Service logs (created at runtime)
```

## System Requirements

- Python 3.8+
- Node.js 14+
- Docker and Docker Compose
- rclone (installed automatically via Docker)
- 4GB RAM minimum
- 10GB disk space for logs and temporary files

## Configuration

### Storage Endpoints

Configure your storage endpoints through the web interface:

1. **S3**: Requires AWS access key, secret key, and region
2. **SMB/CIFS**: Requires host, share name, username, password, and optional domain
3. **SFTP**: Supports password or SSH key authentication
4. **Local**: Specify directory paths on the server

### Environment Variables

Key configuration options in `backend/.env`:
```bash
# Database connection
DATABASE_URL=postgresql://user:pass@localhost:5433/fileorbit

# AWS credentials for S3
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_DEFAULT_REGION=us-east-1

# Email notifications (optional)
SMTP_HOST=smtp.yourdomain.com
SMTP_PORT=587
```

## Deployment

For production deployment:

1. **Security**: Enable authentication and use HTTPS
2. **Monitoring**: Configure Prometheus metrics and alerts
3. **High Availability**: Deploy multiple workers behind a load balancer
4. **Logging**: Use centralized logging (ELK stack or similar)

See [Architecture Documentation](docs/ARCHITECTURE.md) for detailed deployment guidance.

## Support

- **Documentation**: Check the [docs/](docs/) directory for detailed guides
- **Issues**: Report bugs or request features via GitHub issues
- **Implementation Status**: See [IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) for current capabilities