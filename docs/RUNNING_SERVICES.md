# Running PBS Rclone MVP Services

## Quick Start with Management Script

The easiest way to manage all services is using the provided `manage.sh` script:

```bash
# Start everything
./manage.sh start

# Check status
./manage.sh status

# Stop everything
./manage.sh stop
```

## Service Management Details

### Using the Management Script

```bash
# Start specific service
./manage.sh start backend
./manage.sh start worker
./manage.sh start event-monitor

# Stop specific service
./manage.sh stop frontend

# Restart service
./manage.sh restart worker

# View logs
./manage.sh logs backend
./manage.sh logs event-monitor
```

### Manual Service Management

If you prefer to run services manually:

#### 1. Infrastructure (Docker)
```bash
# Start Docker containers
docker-compose up -d

# Check container status
docker ps

# View logs
docker logs pbs-rclone-postgres
docker logs pbs-rclone-redis

# Stop containers
docker-compose down
```

#### 2. Backend API
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

#### 3. Frontend
```bash
cd frontend
npm start

# UI will be available at http://localhost:3000
```

#### 4. Worker Service
```bash
cd backend
source venv/bin/activate
python worker.py

# Worker processes jobs from Redis queue
```

#### 5. Event Monitor Service
```bash
cd backend
source venv/bin/activate
python event_monitor_service.py

# Monitors file system for changes
```

#### 6. Scheduler Service
```bash
cd backend
source venv/bin/activate
python scheduler_service.py

# Executes scheduled jobs based on cron expressions
```

## Service Dependencies

Services must be started in this order:
1. Docker containers (PostgreSQL, Redis)
2. Backend API
3. Frontend (optional, for UI access)
4. Worker (for processing transfers)
5. Event Monitor (for event-driven transfers)
6. Scheduler (for scheduled transfers)

## Monitoring Services

### Check Service Status
```bash
# Using management script
./manage.sh status

# Check specific processes
ps aux | grep -E "(uvicorn|worker|event_monitor|scheduler)"

# Check Docker containers
docker ps

# Check if ports are listening
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
```

### View Logs

Log files are created in the `logs/` directory when using `manage.sh`:
- `logs/backend.log` - API server logs
- `logs/frontend.log` - React development server
- `logs/worker.log` - Job processing logs
- `logs/event-monitor.log` - File system events
- `logs/scheduler.log` - Scheduled job execution

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it pbs-rclone-postgres psql -U pbs_rclone -d pbs_rclone

# Common queries
\dt                    # List tables
SELECT * FROM jobs;    # View jobs
SELECT * FROM endpoints; # View endpoints
\q                     # Quit

# Or use Adminer (if enabled)
docker-compose --profile dev up adminer
# Visit http://localhost:8080
```

### Redis Monitoring

```bash
# Connect to Redis CLI
docker exec -it pbs-rclone-redis redis-cli

# Common commands
KEYS *                 # List all keys
LLEN pbs_rclone:job_queue  # Check job queue length
LRANGE pbs_rclone:job_queue 0 -1  # View queued jobs
```

## Troubleshooting

### Service Won't Start
- Check if ports are already in use
- Verify virtual environment is activated
- Check Docker is running
- Review log files for errors

### Worker Not Processing Jobs
- Verify Redis is running
- Check worker logs for errors
- Ensure rclone is installed (`brew install rclone`)

### Event Monitor Not Detecting Files
- Check file permissions
- Verify watch paths exist
- Review event rules configuration

### Database Connection Issues
- Ensure PostgreSQL container is running
- Check connection string in `.env`
- Verify database initialization completed

## Production Considerations

The current setup is optimized for development. For production:

1. Use a process manager (systemd, supervisor)
2. Configure proper logging rotation
3. Set up monitoring (Prometheus, Grafana)
4. Use environment-specific configurations
5. Implement proper error alerting
6. Consider containerizing all services