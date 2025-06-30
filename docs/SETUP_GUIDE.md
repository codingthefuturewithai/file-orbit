# CTF Rclone MVP Setup Guide

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

## Quick Start Guide

For the simplest setup, use the `manage.sh` script to start all services and initialize the project.

### Step 1: Clone the Repository
```bash
cd /Users/tkitchens/projects/consumer-apps/file-orbit
```

### Step 2: Set Up Environment Variables

The backend requires a `.env` file:
```bash
cd backend
cp .env.example .env
# Edit .env to add your AWS credentials if using S3
cd ..
```

### Step 3: Set Up the Backend
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a Python virtual environment:
   ```bash
   python3 -m venv venv
   ```

3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Step 4: Set Up the Frontend
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

### Step 5: Start All Services
```bash
./manage.sh start
```

### Step 6: Verify Services
```bash
./manage.sh status
```

- **Frontend (UI)**: [http://localhost:3000](http://localhost:3000)
- **Backend (API)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

# Detailed Setup Instructions

For advanced users or troubleshooting, follow these detailed steps:

## Step 1: Set Up Environment Variables
```bash
cp .env.example .env
```

## Step 2: Start Infrastructure Services
```bash
docker-compose up -d
```

## Step 3: Set Up the Backend
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a Python virtual environment:
   ```bash
   python3 -m venv venv
   ```

3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Step 4: Initialize and Seed the Database
1. Create the database tables:
   ```bash
   python init_db.py
   ```

2. Seed the database with test data:
   ```bash
   python seed_db.py
   ```

## Step 5: Start the Backend Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 6: Set Up the Frontend
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the frontend development server:
   ```bash
   npm start
   ```

## Testing the Current State

### What Works Now:
1. **Backend Health Check**: Visit http://localhost:8000/health
   - Should return: `{"status":"healthy","service":"ctf-rclone-mvp","version":"0.1.0"}`

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
   - Username: `ctf_rclone`
   - Password: `ctf_rclone_password`
   - Database: `ctf_rclone`
4. **Testing transfers**: Use `manage.sh` to start all services easily

## Summary

The MVP is fully functional with:
- Complete frontend UI (React + TypeScript)
- Working backend with all API endpoints
- Safe file transfers using temporary files
- Optional checksum verification
- Event-driven and manual transfers
- Infrastructure services via Docker