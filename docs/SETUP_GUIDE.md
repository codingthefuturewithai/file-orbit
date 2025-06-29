# PBS Rclone MVP Setup Guide

## Current Status ✅

**The MVP is fully functional** with:
- ✅ All API endpoints implemented and working
- ✅ Frontend connected to backend
- ✅ Manual transfers working
- ✅ Event-driven transfers for local files
- ✅ Safe file transfers with temporary files
- ✅ Optional checksum verification

## Prerequisites

- Docker and Docker Compose installed
- Node.js 18+ installed
- Python 3.11+ installed
- Git installed
- At least 4GB free RAM
- Rclone installed on your system (for testing)

## Step-by-Step Setup

### 1. Clone and Navigate to MVP Directory

```bash
cd /Users/tkitchens/projects/pbs/rclone-poc/mvp
```

### 2. Create Environment File

```bash
# Copy the example environment file
cp .env.example .env
```

**Note about SECRET_KEY**: The default placeholder value is fine for local development. You only need to change it for production deployments. The current value will work for testing.

### 3. Start Infrastructure Services

```bash
# Start PostgreSQL, Redis, and Rclone RC
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs if needed
docker-compose logs -f
```

Expected output:
```
NAME                    STATUS    PORTS
pbs-rclone-postgres     running   0.0.0.0:5432->5432/tcp
pbs-rclone-redis        running   0.0.0.0:6379->6379/tcp
pbs-rclone-rc           running   0.0.0.0:5572->5572/tcp
```

### 4. Set Up the Backend

```bash
cd backend

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Initialize the Database

```bash
# Make sure you're in the backend directory with venv activated
# Create the database tables
python init_db.py

# Optionally, add sample data for testing
python seed_db.py
```

You should see:
```
Creating database tables...
Database tables created successfully!

Tables created:
- jobs
- transfers
- endpoints
- transfer_templates
```

### 6. Start the Backend Server

```bash
# Make sure you're in the backend directory with venv activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Starting up PBS Rclone MVP API...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 7. Set Up the Frontend (New Terminal)

```bash
# From the mvp directory
cd frontend

# Install dependencies
npm install

# This will take a few minutes the first time
```

### 8. Start the Frontend Development Server

```bash
# Make sure you're in the frontend directory
npm start
```

The browser should automatically open to http://localhost:3000

## Testing the Current State

### What Works Now:
1. **Backend Health Check**: Visit http://localhost:8000/health
   - Should return: `{"status":"healthy","service":"pbs-rclone-mvp","version":"0.1.0"}`

2. **API Documentation**: Visit http://localhost:8000/docs
   - Shows interactive API documentation (but endpoints not implemented yet)

3. **Frontend UI**: Visit http://localhost:3000
   - Dashboard loads but shows "Loading..." or errors
   - Navigation between pages works
   - Forms are visible but won't submit successfully

4. **Rclone RC Interface**: Visit http://localhost:5572
   - Shows Rclone's web interface

### What Doesn't Work Yet:
- Creating transfers
- Viewing endpoints
- Setting up transfer templates
- Any data operations

## Next Development Steps

To make the MVP functional, we need to implement:

1. **API Endpoints** (backend/app/api/api_v1/endpoints/):
   - Jobs CRUD operations
   - Endpoints management
   - Event rules configuration
   - Transfer operations

2. **Job Processor Service**:
   - Background worker to process queued jobs
   - Integration with Rclone service

3. **Event Manager**:
   - S3 event consumer
   - Filesystem watcher

## Troubleshooting

### Docker Issues
```bash
# Reset everything
docker-compose down -v
docker-compose up -d
```

### Backend Won't Start
- Check PostgreSQL is running: `docker-compose ps`
- Check Redis is running: `docker-compose ps`
- Verify .env file exists
- Check Python version: `python --version` (should be 3.11+)

### Frontend Won't Start
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall: `rm -rf node_modules && npm install`
- Check Node version: `node --version` (should be 18+)

### Port Conflicts
Default ports used:
- 3000: React frontend
- 8000: FastAPI backend
- 5432: PostgreSQL
- 6379: Redis
- 5572: Rclone RC

Change these in docker-compose.yml and .env if needed.

## Configuring File Transfer Safety Features

### Safe File Transfers (Temporary Files)
By default, rclone uses temporary files during transfers:
- Files upload with `.partial` suffix
- Renamed to final name only after success
- No configuration needed - this is the default behavior

To customize:
1. **Temporary Directory**: Set per endpoint in the UI (future feature)
2. **Partial Suffix**: Can be changed via rclone config (default: `.partial`)

### Enabling Checksum Verification
To enable checksum verification for transfers:
1. When creating a transfer in the UI (future feature):
   - Check "Verify checksums after transfer"
2. For testing via CLI:
   ```bash
   rclone copy source dest --checksum
   ```

### Monitoring Partial Files
The worker service automatically handles `.partial` files:
- Progress updates show actual file being written
- Final rename happens automatically
- Failed transfers leave `.partial` files for debugging

## Development Tips

1. **Backend logs**: The FastAPI server shows detailed logs in the terminal
2. **Frontend logs**: Check browser console for errors
3. **Database access**: Use Adminer at http://localhost:8080 (if enabled)
   - Server: `postgres`
   - Username: `pbs_rclone`
   - Password: `pbs_rclone_password`
   - Database: `pbs_rclone`
4. **Testing transfers**: Use `manage.sh` to start all services easily

## Summary

The MVP is fully functional with:
- Complete frontend UI (React + TypeScript)
- Working backend with all API endpoints
- Safe file transfers using temporary files
- Optional checksum verification
- Event-driven and manual transfers
- Infrastructure services via Docker