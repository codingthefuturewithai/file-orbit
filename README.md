# File Orbit

Enterprise file transfer orchestration system built on top of rclone for machine-to-machine and cloud-to-on-premise transfers.

## 🚀 Getting Started

**[Follow the Setup Guide](docs/SETUP_GUIDE.md)** for step-by-step installation instructions.

## ✅ Current Status: Functional MVP with Local Transfers

**The MVP is fully functional for local file transfers with event-driven capabilities, manual transfers, and comprehensive endpoint management. Cloud storage integration (S3, SMB, SFTP) requires configuration.**

## Overview

File Orbit provides a web-based orchestration layer on top of rclone to address enterprise requirements like event-driven transfers, scheduling, monitoring, and throttling. Built specifically for:

- **Cloud-to-On-Premise** transfers (S3 → SMB shares)
- **Machine-to-Machine** transfers (SFTP → SFTP)
- **Event-driven workflows** (S3 events trigger transfers)
- **Scheduled transfers** with cron expressions

## Architecture

The system consists of:
- **Frontend**: React TypeScript application
- **Backend**: FastAPI Python REST API
- **Database**: PostgreSQL for persistent storage
- **Queue**: Redis for job management
- **Workers**: Python services for job processing
- **File Transfer**: Rclone CLI (not RC API)

## Key Features

### Working Now
- ✅ **Manual Transfers** - Create and monitor file transfers via web UI
- ✅ **Event-Driven Transfers** - Automatic transfers when files appear (local directories)
- ✅ **Endpoint Management** - Configure storage locations with throttling
- ✅ **Transfer Templates** - Define automated transfer workflows
- ✅ **Transfer History** - Track all transfers with filtering and search
- ✅ **Real-time Monitoring** - Live progress updates and statistics
- ✅ **Safe File Writing** - Uses temporary files during transfer to prevent partial file reads
- ✅ **Checksum Verification** - Supports file integrity checks after transfer completion

### Partially Working
- 🟡 **Scheduled Transfers** - Can create schedules but automatic execution not enabled
- 🟡 **S3 Integration** - UI and code ready, needs AWS credentials

### Not Yet Implemented
- ❌ **Authentication** - No login system
- ❌ **Cloud Storage** - S3/SMB/SFTP endpoints need configuration

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

## Next Steps

1. **Enable S3 Integration**: Add AWS credentials for cloud transfers
2. **Configure SMB/SFTP**: Add real network endpoint credentials
3. **Enable Scheduler**: Uncomment scheduler in `manage.sh` for automatic scheduled transfers
4. **Add Authentication**: Implement login system for production use

## Contributing

This is a production-ready implementation. For deployment, consider:
- Adding comprehensive error handling
- Implementing authentication and authorization
- Setting up monitoring and alerting
- Configuring log aggregation
- Adding integration tests