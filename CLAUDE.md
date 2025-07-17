# FileOrbit Project Memory (Condensed)

## Quick Status for Next Session
- **Current Date**: July 16, 2025
- **Git Status**: Main branch, 21 commits ahead of origin (all local)
- **Last Work**: Partially completed CP-6 (chain rules), created bug CP-9 for batch transfer fix
- **Services**: All should be stopped - run `./manage.sh start all` to resume
- **Key Issue**: Chain rules only work for single files, not batch transfers (see CP-9)

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
  - Template selection in Create Transfer (CP-1 fixed)

## Session Resume Instructions
```bash
cd /Users/timkitchens/projects/consumer-apps/file-orbit
./manage.sh start all
# Access UI at http://localhost:3000
```

### Frontend Management (FIXED July 16, 2025)
The manage.sh script now properly kills ALL frontend processes:
- Kills processes on ports 3000-3010 (Vite's range)
- Kills npm and vite processes by name
- Frontend ALWAYS uses port 3000 (no more port hopping)
- If port 3000 is busy, it attempts cleanup before failing

### Individual Services
- Backend: `./manage.sh start backend`
- Frontend: `./manage.sh start frontend` (uses npm run dev for Vite)
- Worker: `./manage.sh start worker`
- Event Monitor: `./manage.sh start event-monitor`

## Known Issues & Next Steps
See `frontend/KNOWN_ISSUES.md` for current bugs and missing features:
1. **CP-1**: ~~Template selection validation bug~~ ✅ FIXED
2. **CP-4**: ~~Settings persistence not implemented~~ ✅ COMPLETED
3. **CP-5**: Transfer functionality needs testing
4. **CP-6**: ~~Chain rules functionality~~ ✅ COMPLETED
5. **CP-7**: Error handling improvements
6. **CP-8**: Dark theme consistency
7. **CP-9**: ~~Chain rules fail for batch transfers~~ ✅ FIXED

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
- Main branch has all features merged locally (21 commits ahead of origin)
- Create feature branches: `fix/CP-[number]-description` for bugs, `feature/CP-[number]-description` for features
- Local merge workflow supported via `/merge-issue` command
- Latest commit: Fixed chain rules for batch transfers (CP-9)

## Recent Changes (Session of July 16, 2025)
- Fixed manage.sh frontend handling:
  - Now properly kills ALL frontend processes (npm and vite)
  - Frontend always uses port 3000 (no more port hopping)
  - Cleans up processes on ports 3000-3010
- Completed CP-6: Chain rules functionality
  - Fixed event monitor bug (chain_templates → chain_rules)
  - Created ChainJobService for centralized chain job management
  - Added POST /transfer-templates/{id}/execute endpoint
  - Updated worker to properly detect chain jobs via parent_job_id
  - Added Execute button to Templates page UI
  - Added chain indicators in transfer lists (badge and icon)
  - Created comprehensive test suite
- Fixed SMB Transfer Issues:
  - Root cause: Transfer template destination path was corrupted (lost share name prefix)
  - Fix: Added share field to worker.py SMB config (line 262)
  - CRITICAL: SMB destination paths MUST include share name (e.g., `file-orbit-transfers/{filename}`)
  - Data corruption was caused by `update_test_endpoints.py` script overwriting production data
  - Script renamed to `DANGEROUS_DO_NOT_USE_update_test_endpoints.py` to prevent future issues
  - SMB transfers now working correctly after template destination path fixed
- Fixed Transfer History date filtering (Mantine v8 compatibility):
  - DatePickerInput now properly handles string dates in 'YYYY-MM-DD' format
  - Added "Today" and "Last 7 days" convenience buttons
  - Date ranges are inclusive of both start and end dates
- Fixed CP-9: Chain Rules for Batch Transfers (COMPLETED):
  - ✅ Chain rules now work for ALL transfer types (single, batch, event-driven, manual)
  - Fixed "can't limit to single files when using filters" rclone error
  - Root cause: Chain jobs had full file path as source_path with wildcard pattern
  - Solution: Split path properly - directory as source_path, filename as file_pattern
  - Created fix script to repair existing chain jobs in database
  - Successfully tested batch transfer of 9 files from Local → SMB → Local
  - All chain transfers completed successfully

## Recent Changes (Session of July 15, 2025)
- Fixed CP-1: Template selection validation bug in CreateTransferForm
- Improved Create Transfer modal layout (size xl)
- Removed Stepper descriptions for better horizontal layout
- Fixed unused imports in CreateTransferForm
- Completed CP-4: Settings persistence implementation
  - Created settings database model with encryption for sensitive fields
  - Implemented full REST API for settings management
  - Updated frontend Settings page to use API instead of hardcoded values
  - Added loading states and error handling
  - Implemented reset to defaults functionality for each section
  - Created comprehensive test suite (12 passing tests)
- All changes merged to main locally (not pushed to remote)

## Important Files
- `CLAUDE.md` - This memory file
- `frontend/KNOWN_ISSUES.md` - Current bugs and todos
- `manage.sh` - Service management
- `docs/ARCHITECTURE.md` - System design
- `docs/FEATURES.md` - Feature status

## Available Documentation via RAG Retriever
IMPORTANT: Always use RAG retriever for framework-specific questions instead of guessing:
- `mantine_v7_docs` collection - Complete Mantine v7 documentation
- `claude_code_docs` collection - Claude Code documentation
- `mcp_python_sdk_docs` collection - MCP Python SDK documentation
Use: `mcp__rag-retriever__vector_search` with collection_name parameter

## CRITICAL: Frontend Port Verification
When reporting frontend status, ALWAYS verify the actual port:
```bash
ps aux | grep -E "vite|npm run dev" | grep -v grep
lsof -p [PID] -P | grep LISTEN
```
NEVER assume port 3000 without verification!

## CRITICAL RULE: Frontend Changes = MANDATORY VERIFICATION
After ANY frontend code changes:
1. ALWAYS run: `ps aux | grep -E "vite|npm run dev" | grep -v grep`
2. If no process found, the frontend is NOT running - DO NOT claim it is
3. If you start the frontend, WAIT for it to fully start before claiming it's ready
4. NEVER say "frontend is running on port X" without verification
5. ALWAYS tell the user they need to start/restart the frontend after changes

VIOLATION OF THIS RULE IS UNACCEPTABLE.

## CRITICAL RULE: Follow Existing Code Patterns
When implementing ANY new feature:
1. FIRST search for existing similar functionality in the codebase
2. ANALYZE how existing code handles similar tasks
3. STRICTLY FOLLOW the existing patterns unless there's a clear reason not to
4. If existing pattern seems wrong, STOP and present findings to user for decision
5. NEVER assume a new approach is better without checking existing code

Examples of patterns to check:
- How services are initialized (singletons vs instances)
- How API endpoints structure responses
- How database connections are managed
- How imports are organized
- Error handling patterns
- Testing patterns

VIOLATION: Creating new patterns without following existing ones causes bugs and inconsistency.

## TODO: Document Existing Patterns
Need to create comprehensive documentation of all recurring patterns:
- Service initialization patterns (e.g., redis_manager singleton)
- API response patterns
- Database transaction patterns
- Error handling conventions
- Testing conventions
- Import organization rules