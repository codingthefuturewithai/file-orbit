# CTF Rclone MVP

## ✅ Current Status: Functional MVP with Local Transfers

**The MVP is fully functional for local file transfers with event-driven capabilities, manual transfers, and comprehensive endpoint management. Cloud storage integration (S3, SMB) requires configuration.**

## Recent Changes (June 29, 2025)

### Major Refactoring: Event Rules → Transfer Templates
- **Renamed "Event Rules" to "Transfer Templates"** throughout the entire codebase for better clarity
- **Fixed critical job execution bug** where jobs were stuck in "queued" status due to database column mismatches
- **Completed database migration** from `event_rules` table to `transfer_templates` table
- **Fixed worker service** to properly process jobs from the Redis queue
- **Updated all UI components** to use consistent "Transfer Template" terminology

### Scheduled Execution Framework (In Progress)
- **Added scheduler service** (`scheduler_service.py`) for cron-based job execution
- **Implemented cron expression validation** and testing utilities
- **Created scheduled job management** in the API and database
- **Note:** Scheduler service exists but is not yet integrated into `manage.sh` startup

## Overview

This is the Minimum Viable Product (MVP) implementation of the CTF Rclone enterprise file transfer solution. The MVP provides a web-based orchestration layer on top of rclone for **machine-to-machine** and **cloud-to-on-premise** transfers, with a focus on event-driven workflows.

## Quick Start

```bash
# Prerequisites
brew install rclone  # Required for file transfers

# Start all services
./manage.sh start

# Check status
./manage.sh status

# Access the application
# UI: http://localhost:3000
# API: http://localhost:8000/docs
```

## Documentation

- 📐 [Architecture Overview](ARCHITECTURE.md) - System design and components
- 🚀 [Running Services](RUNNING_SERVICES.md) - How to start, stop, and manage services  
- ✨ [Features Guide](FEATURES.md) - Current capabilities and limitations
- 🛠️ [Setup Guide](SETUP_GUIDE.md) - Detailed installation instructions

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
- ❌ **Email Notifications** - Structure exists but not configured

## Architecture Summary

The system consists of:
- **Frontend**: React TypeScript application
- **Backend**: FastAPI Python REST API
- **Database**: PostgreSQL for persistent storage
- **Queue**: Redis for job management
- **Workers**: Python services for job processing
- **File Transfer**: Rclone CLI (not RC API)

**IMPORTANT**: Current MVP only supports transfers on the local server. Production requires distributed architecture where a single UI can orchestrate transfers between ANY servers (e.g., UI on Server A initiates transfer from Server B to Server C).

See [ARCHITECTURE.md](ARCHITECTURE.md) for current design and [DISTRIBUTED_ARCHITECTURE.md](DISTRIBUTED_ARCHITECTURE.md) for production requirements.

## Testing the MVP

### Test Manual Transfer
```bash
# Create a test file
echo "test content" > /tmp/test-video.mp4

# Use the UI to create a transfer
# 1. Go to http://localhost:3000
# 2. Click "Create Transfer"
# 3. Select source and destination
# 4. Execute and monitor progress
```

### Test Event-Driven Transfer
```bash
# Set up event monitoring
cd backend && python test_event_driven.py

# Trigger a transfer
python test_event_driven.py --trigger

# Or manually drop a file
cp video.mp4 /tmp/ctf-rclone-test/watch/
```

## Project Structure
```
mvp/
├── manage.sh         # Service management script
├── backend/          # FastAPI backend
│   ├── app/         # Application code
│   ├── worker.py    # Job processor
│   ├── event_monitor_service.py  # File watcher
│   └── scheduler_service.py      # Cron scheduler
├── frontend/        # React frontend
│   └── src/        # React components
├── docker-compose.yml  # Infrastructure services
└── logs/           # Service logs (created at runtime)
```

## Development

### Backend Development
```bash
cd backend
source venv/bin/activate
python -m pytest  # Run tests
python -m uvicorn app.main:app --reload  # Run with auto-reload
```

### Frontend Development
```bash
cd frontend
npm test        # Run tests
npm run build   # Production build
```

## API Documentation

When the backend is running, visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

## Troubleshooting

### Common Issues
1. **Services won't start**: Check if ports are in use
2. **Transfers fail**: Ensure rclone is installed
3. **Event monitoring not working**: Check file permissions
4. **Database errors**: Verify PostgreSQL is running

See [RUNNING_SERVICES.md](RUNNING_SERVICES.md) for detailed troubleshooting.

## Next Steps (Phase 1 - Week 1)

### Day 1-2: S3 & Log Viewer (Start Here!)
1. **Add S3 Credentials** (30 minutes)
   ```bash
   # Add to backend/.env
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   AWS_REGION=us-east-1
   ```
2. **Test S3 Transfer** - Create S3 endpoint in UI and test manual transfer
3. **Implement Log Viewer** (3 hours) - Backend endpoint + UI component

### Day 3-4: SMB Implementation
4. **Update rclone_service.py** - Add SMB configuration (3 hours)
5. **Test with Windows Shares** - Verify SMB transfers work

### Day 5: SFTP Implementation  
6. **Update rclone_service.py** - Add SFTP configuration (3 hours)
7. **Test with SFTP Servers** - Both password and key auth

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for complete 6-week roadmap to production.

## Contributing

This is an MVP implementation. For production deployment, consider:
- Adding comprehensive error handling
- Implementing authentication and authorization
- Setting up monitoring and alerting
- Configuring log aggregation
- Adding integration tests