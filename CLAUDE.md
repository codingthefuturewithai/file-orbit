# FileOrbit Project Memory (Condensed)

## Project Overview
FileOrbit is an enterprise UI layer built on top of rclone for video file transfers. It provides a web-based orchestration layer that addresses rclone's limitations for enterprise use, specifically for CTF's video transfer needs.

### Core Features
- Web-based UI for job management (Mantine UI with TypeScript)
- Backend API wrapping rclone RC commands (FastAPI)
- Support for S3, SMB/CIFS, SFTP, and local transfers
- Transfer templates with event-based triggers
- Real-time progress monitoring
- Audit logging and failed transfer recovery

## Current Status (July 15, 2025)
- **Frontend**: Mantine UI implementation is now the primary frontend (replaced legacy React)
- **Backend**: FastAPI with PostgreSQL, Redis, and rclone integration
- **Working Features**:
  - S3 transfers with AWS credentials
  - SMB/CIFS transfers with proper authentication
  - SFTP transfers with key/password auth
  - Local directory transfers
  - Manual and scheduled transfers
  - Transfer templates (formerly event rules)
  - Real-time progress monitoring
  - Log viewer UI

## Session Resume Instructions
```bash
cd /Users/timkitchens/projects/consumer-apps/file-orbit
./manage.sh start all
# Access UI at http://localhost:3000
```

### Individual Services
- Backend: `./manage.sh start backend`
- Frontend: `./manage.sh start frontend` (uses npm run dev for Vite)
- Worker: `./manage.sh start worker`
- Event Monitor: `./manage.sh start event-monitor`

## Known Issues & Next Steps
See `frontend/KNOWN_ISSUES.md` for current bugs and missing features:
1. **CP-1**: Template selection validation bug
2. **CP-4**: Settings persistence not implemented
3. **CP-5**: Transfer functionality needs testing
4. **CP-6**: Chain rules functionality
5. **CP-7**: Error handling improvements
6. **CP-8**: Dark theme consistency

## Project Structure
```
file-orbit/
├── backend/          # FastAPI backend with rclone integration
├── frontend/         # Mantine UI (TypeScript + Vite)
├── docs/            # Architecture and implementation docs
├── logs/            # Service logs
├── manage.sh        # Service management script
└── docker-compose.yml
```

## Key Technical Details
- **Rclone Integration**: Uses RC API on port 5572
- **Frontend**: Vite + React + TypeScript + Mantine UI
- **Backend**: FastAPI + PostgreSQL + Redis
- **Throttling**: Implemented at job level (needs fixing for file-level)

## Testing Transfers
```bash
# Setup test data
cd backend
python setup_test_data.py
python update_test_endpoints.py

# Create transfer via UI
# Monitor in worker terminal
```

## Git Workflow
- Main branch has all features merged
- Create feature branches: `feature/CP-[number]-description`
- Local merge workflow supported via `/merge-issue` command

## Important Files
- `CLAUDE.md` - This memory file
- `frontend/KNOWN_ISSUES.md` - Current bugs and todos
- `manage.sh` - Service management
- `docs/ARCHITECTURE.md` - System design
- `docs/FEATURES.md` - Feature status

## CRITICAL: Frontend Port Verification
When reporting frontend status, ALWAYS verify the actual port:
```bash
ps aux | grep -E "vite|npm run dev" | grep -v grep
lsof -p [PID] -P | grep LISTEN
```
NEVER assume port 3000 without verification!