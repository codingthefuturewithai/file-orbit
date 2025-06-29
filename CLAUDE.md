# Project Memory: Rclone Enterprise UI Layer

## Project Summary
This project builds an enterprise UI layer on top of rclone for video file transfers.

## Project Overview
Building a custom enterprise file transfer solution using rclone as the underlying engine, with a specific focus on video file transfers (mp4, mov, mxf formats). The goal is to create a web-based orchestration layer that addresses rclone's limitations for enterprise use at CTF.

## Key Components Created

### 1. Enhanced Interactive UI Mockup (`rclone-ui-mockup-enhanced.html`)
- Fully functional HTML prototype with interactive features
- Dashboard with real-time transfer monitoring and progress bars
- CTF logo integration in dashboard header
- Job creation and management interface with validation
- Schedule configuration for recurring transfers (hourly, daily, weekly)
- Remote storage management supporting SMB/CIFS, S3, SFTP, and local filesystems
- Comprehensive logging with 4 tabs: System, Transfer, Audit Trail, Notifications
  - Fixed tab switching bug that prevented Audit Trail and Notifications from displaying
- Failed transfer recovery mechanisms with retry functionality
- Toast notifications for user feedback
- Dropdown action menus (pause, resume, retry, cancel)
- **NEW: Fully functional Settings section with 4 tabs:**
  - General: Binary paths, log levels, atomic delivery configuration
  - Performance: Transfer settings, resource monitoring, Prometheus metrics
  - Notifications: Email configuration (smtp.ctf.org), webhook integration, event triggers
  - Security: LDAP/AD authentication, API security, compliance modes

### 2. Technical Documentation
- **rclone-functional-gap-analysis.md**: Identifies gaps between rclone capabilities and enterprise needs
- **rclone-detailed-research.md**: Deep technical dive into rclone RC API, configuration, and integration
- **DELIVERABLES-SUMMARY.md**: Executive summary of the solution and addressed gaps
- **ENHANCED-MOCKUP-SUMMARY.md**: Details of the enhanced UI features

## Identified Functional Gaps in Rclone
1. **No native scheduling** - Requires external cron/scheduler
2. **No event-based triggers** - No file system watching
3. **CLI-only interface** - No web UI for job management
4. **Limited notifications** - Only exit codes, no email/webhook alerts
5. **No atomic delivery** - Missing staging and rename workflow
6. **Basic audit logging** - No comprehensive user action trails

## Solution Architecture
The custom orchestration layer provides:
- Web-based UI for job management and monitoring
- Backend API wrapping rclone RC commands
- Scheduler service for recurring transfers
- Event monitoring for trigger-based transfers
- Notification system for alerts
- Audit database for compliance
- Atomic delivery through temp directory staging

## Technical Implementation Details
- Uses rclone RC (Remote Control) API on port 5572
- Prometheus metrics endpoint for monitoring
- Supports authentication via basic auth, certificates, or htpasswd
- Example integrations provided in Python and JavaScript
- Focus on video file workflows with realistic paths and filenames

## Current Status (June 29, 2025 - Fresh Repository)
- **Repository**: Migrated to `/Users/tkitchens/projects/consumer-apps/file-orbit/`
- **Git Status**: Fresh repository (will be initialized with `git init`)
- **Working Features (Local Only)**:
  - Local directory → Local directory transfers
  - File watching on local directories  
  - Manual transfer creation via UI
  - Transfer history and monitoring
  - Basic job queue processing
  - Log Viewer UI (implemented June 29)
- **Major Refactoring Completed**:
  - Renamed "Event Rules" to "Transfer Templates" throughout codebase
  - Fixed critical job execution bugs (jobs stuck in queued status)
  - Database migration from event_rules to transfer_templates table
- **Scheduled Execution Framework**: Created but not integrated
  - Scheduler service (`scheduler_service.py`) complete
  - Test scripts for scheduled jobs complete
  - Not enabled in manage.sh startup
- **NOT Working (Required for Production)**:
  - S3 transfers - No AWS credentials configured
  - SMB/CIFS transfers - Never tested with real Windows shares
  - SFTP transfers - No SSH key management
  - S3 event monitoring - SQS integration not implemented
  - Cross-machine transfers - Only local paths work
  - Network error handling - No retry logic
  - Credential security - Stored in plain text

## Historical Status (December 20, 2024 - MVP Scaffolding Complete!)
- **Project Reorganization Completed**:
  - Created clear directory structure (docs/, ui-mockups/, assets/, working-files/)
  - Added comprehensive README with two-pronged approach explanation
  - Fixed all internal references (diagram paths, logo paths)
- **MVP Documentation Finalized**:
  - MVP architecture document with simplified deployment
  - MVP implementation plan (6-8 weeks, 4-5 with AI)
  - Fully interactive MVP UI mockup v3 with proper navigation
  - Integrated throttling configuration in endpoint settings
- **UI Screenshots Added**:
  - 7 MVP screenshots demonstrating core functionality
  - README updated with visual walkthrough tying each screen to requirements
  - Screenshots show: Dashboard, Endpoints, Create Transfer, Event Rules, History, Monitoring, Settings
- **Key Design Improvements**:
  - Throttling moved from settings to endpoint configuration (more intuitive)
  - Full interactivity in mockups (modals, forms, delete actions)
  - Transfer details modals showing error information
- **Ready for Stakeholder Review**:
  - Clear visual demonstration of MVP capabilities
  - Documented path from MVP to full solution
  - All deliverables easily accessible from README

## Key Design Decisions
1. All examples use video files to match CTF use case
2. Emphasis on SMB/CIFS and UNC path support for Windows shares
3. Failed transfer handling with detailed error tracking
4. Real-time progress monitoring with ETA calculations
5. Maintains strict alignment with rclone's actual capabilities
6. **June 29, 2025**: Refocused on machine-to-machine and cloud-to-on-premise transfers as primary use cases
7. **June 29, 2025**: Recognized that local-only transfers are insufficient for production value

## Important Files
- `rclone-ui-mockup-enhanced.html` - The main interactive prototype (v2 with Settings functionality)
- `ctf.png` - CTF logo file for dashboard branding
- `rclone-functional-gap-analysis.md` - Critical requirements mapping (updated with throttling)
- `rclone-detailed-research.md` - Technical implementation guide
- `rclone-technical-analysis.md` - Deep dive into rclone capabilities and deployment patterns
- `ctf-rclone-architecture.md` - High-level architecture design with Mermaid diagrams
- `DELIVERABLES-SUMMARY.md` - Executive overview
- `ENHANCED-MOCKUP-SUMMARY.md` - Summary of v1 enhancements

## External Documentation
- **Rclone Official Documentation**: https://rclone.org/docs/ - Complete reference for rclone features, flags, and capabilities

## Research Findings & Decisions

### Disk Space Monitoring (Research completed: June 29, 2025)
**Finding**: Rclone does NOT have built-in capability to automatically pause transfers based on disk space thresholds.

**Technical Limitations**:
- `rclone about` command exists but:
  - Not supported by all backends (especially local filesystem, SMB/CIFS)
  - Cannot check space continuously during transfers
  - No automatic pause/resume based on thresholds
- No flags like `--min-disk-space` or similar
- Transfers simply fail when disk is full

**Decision**: DO NOT implement disk space threshold monitoring for MVP
- Cannot reliably check space on Linux/Windows SMB/CIFS shares
- Would require complex wrapper logic with limited backend support
- Better to let transfers fail naturally and handle errors appropriately

### Log File Management Gap (Identified: June 29, 2025)
**Issue**: Log files are currently hardcoded to project directory paths

**Problems**:
- Won't work for production deployments (not cloned repositories)
- Should use standard system locations (e.g., `/var/log/file-orbit/`)
- No log rotation configured
- Paths not configurable via environment variables

**Required Fix**: 
- Phase 3, Week 3 of implementation plan
- Make all log paths configurable
- Support standard deployment patterns
- Implement proper log rotation

## Recent Updates (December 20, 2024)

### UI Mockup v2 Completion
1. **Settings Section Enhancement**: Added full functionality to all Settings tabs
   - Performance tab: Resource monitoring, metrics configuration
   - Notifications tab: CTF-specific email settings, webhook integration
   - Security tab: LDAP authentication for CTF domain, compliance modes
2. **Bug Fixes**: 
   - Fixed JavaScript tab switching for Audit Trail and Notifications tabs
   - Corrected element ID mapping in showLogTab() function
3. **CTF Branding**: Added CTF logo image reference to dashboard header
4. **Code Improvements**: Added showSettingsTab() function for Settings navigation

### Architecture Phase Begun
1. **Requirements Update**: Added endpoint-specific throttling requirement (5TB storage limit example)
2. **Technical Analysis Completed**: 
   - Deep dive into rclone RC API capabilities
   - Verified distributed deployment patterns
   - Confirmed concurrent transfer controls
   - Identified gaps requiring wrapper services
3. **Architecture Design Created**:
   - Three-layer architecture (UI, Business Logic, Orchestration)
   - Kubernetes-native deployment design
   - Throttle Controller for per-endpoint limits
   - Event Manager for S3 notifications
   - Complete data flow diagrams in Mermaid format
4. **Next Step**: Generate architecture diagrams using Mermaid MCP tool

## Lessons Learned
- Tab switching requires careful attention to element IDs matching the JavaScript selectors
- CTF infrastructure uses LDAP/Active Directory for authentication
- CTF email infrastructure uses smtp.ctf.org for notifications
- The mockup successfully demonstrates all identified functional gaps can be addressed
- Rclone RC API provides comprehensive programmatic control but lacks native event handling
- Per-endpoint throttling requires a wrapper service as rclone only supports global limits
- Kubernetes StatefulSet is preferred for rclone deployment to maintain stable configuration
- **UI/UX Design Insights**:
  - Throttling configuration belongs with endpoint definition, not in separate settings
  - Delete actions should provide visual feedback (animation)
  - Modal dialogs improve user experience over inline forms
  - Transfer details need comprehensive error information for troubleshooting
- **Project Organization**:
  - Clear directory structure essential for stakeholder navigation
  - Screenshots in README provide immediate understanding of capabilities
  - Linking UI elements to requirements helps justify design decisions

## MVP Approach (December 20, 2024)

### Core MVP Requirements
1. **Event-Driven Transfers** (Priority #1)
   - S3 events trigger transfers to on-premises
   - On-premises file watching triggers secondary transfers
   - Transfer chains: S3 → Primary → Secondary destinations

2. **Manual Transfer Capability**
   - Basic UI form for ad-hoc transfers
   - Progress monitoring and cancellation

3. **Essential Throttling**
   - Per-endpoint concurrent limits (especially for 5TB storage endpoint)
   - Simple configuration-based approach

4. **Simplified Architecture**
   - Deploy on VMs initially (not Kubernetes)
   - Simple nginx reverse proxy (not sophisticated API gateway)
   - Single Redis/PostgreSQL instances
   - Local auth initially (LDAP later)

### MVP Timeline
- **Traditional Development**: 6-8 weeks
- **AI-Assisted Development**: 4-5 weeks
  - AI scaffolds project structure and boilerplate
  - AI generates API from requirements
  - AI creates UI components from mockup
  - AI writes integration tests
  - Human developers focus on business logic and integration

### What Gets Deferred
- Real-time metrics dashboards
- Complex scheduling (beyond daily/weekly)
- Prometheus/Grafana monitoring
- Advanced authentication (LDAP)
- Kubernetes orchestration
- High availability configurations

### Key Insight
The MVP won't be throwaway - it forms the foundation that can be enhanced incrementally without major rearchitecture.

## MVP Implementation Progress (June 2025)

### ✅ MVP Core Functionality Complete!
1. **Infrastructure Running**:
   - Docker containers: PostgreSQL, Redis, Rclone RC all running
   - Database initialized with tables (jobs, transfers, endpoints, event_rules)
   - Database seeded with sample endpoints and event rules
   - **REQUIRED**: rclone must be installed (`brew install rclone`)
   
2. **Backend Complete**:
   - FastAPI app running on port 8000
   - All API endpoints implemented (endpoints, jobs, event-rules, transfers, stats)
   - Job processor (worker.py) implemented with full transfer capability
   - RcloneService updated with CLI integration for actual transfers
   - Redis queue with delayed job support
   - Transfer progress monitoring
   - Fixed all schema/model mismatches
   - Fixed path handling for local endpoints
   
3. **Frontend Functional**:
   - React TypeScript app with all pages working
   - Endpoints: Full CRUD (Add, Edit, Delete)
   - Jobs: Create manual/scheduled transfers with immediate execution
   - Dashboard: Shows real-time statistics with redirect after job creation
   - Event Rules: Display only (edit not implemented)
   
4. **File Transfers Working**:
   - Successfully tested transfer of *.mp4 files from Local Storage to 5TB Limited Storage
   - Files transferred from /tmp/ctf-rclone-test/source to /tmp/ctf-rclone-test/5tb-limited/transferred/
   - Progress monitoring and completion status updates working

### 🟡 What's Missing for Production
1. **Scheduled Job Execution** - Scheduler service exists but not running automatically
2. **Real S3 Event Monitoring** - S3 code exists but needs AWS credentials and configuration
3. **Authentication** - No login system
4. **Real Cloud Endpoints** - Using local paths for testing (no actual S3/SMB connections)

### How to Test File Transfers
1. **Setup Test Data**:
   ```bash
   cd mvp/backend
   python setup_test_data.py        # Creates test files
   python update_test_endpoints.py  # Updates DB to use test paths
   ```

2. **Start Worker**:
   ```bash
   cd mvp/backend
   source venv/bin/activate
   python worker.py  # Run in separate terminal
   ```

3. **Create Transfer**:
   - Go to http://localhost:3000
   - Click "Create Transfer"
   - Select endpoints and paths
   - Click "Create & Execute"

4. **Monitor**:
   - Check worker terminal for progress
   - View files in destination: `ls /tmp/ctf-rclone-test/*/`

### Session Resume Instructions
If resuming in a new session:
1. **CRITICAL**: Ensure rclone is installed: `brew install rclone`
2. Start Docker: `docker-compose up -d` (in mvp directory)
3. Start backend: `cd mvp/backend && source venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
4. Start frontend: `cd mvp/frontend && npm start`
5. Start worker: `cd mvp/backend && source venv/bin/activate && python worker.py`
6. Test transfers using the UI!

### Major Fixes Completed (June 26, 2025)
1. **Retry Functionality**: Implemented retry for failed transfers with UI state management
2. **Job Details Modal**: Created comprehensive modal showing all job information, transfer details, and progress
3. **Transfer History Page**: 
   - Added filtering by status, type, search term, and date range
   - Implemented pagination with items per page selector (10, 25, 50, 100)
   - Fixed date filtering timezone issues
4. **Timezone Handling**: Fixed worker using datetime.now(timezone.utc) instead of datetime.utcnow()
5. **API Improvements**:
   - Jobs now ordered by created_at DESC (newest first)
   - Added missing fields to JobResponse schema (started_at, completed_at, etc.)
   - Stats endpoint now correctly counts jobs instead of transfers
6. **UI/UX Fixes**:
   - Dashboard clearly shows "10 Most Recent Transfers"
   - Removed confusing "View All" links
   - Fixed modal positioning to center on screen
   - All timestamps display in user's local timezone (EDT)

### Completed MVP Features (June 26, 2025 - Evening Update)
1. ✅ **Event Rules CRUD** (feature/event-rules-crud) - COMPLETE
   - Frontend edit/delete functionality working
   - Create new event rules via UI
   - Fixed critical modal display bug in index.css

2. ✅ **Event-Driven Transfers** (feature/event-driven-transfers) - COMPLETE (Local Only)
   - File system watcher monitors LOCAL directories for changes
   - S3 event listener code exists but NOT configured/working
   - Transfer chains fully implemented (Local → Local destinations only)
   - Pattern matching and path templating
   - Test script provided for demonstration
   - Fixed Redis connection and method name issues (June 27)

### Remaining MVP Features (Priority Order)
3. **Scheduled Job Execution** (feature/scheduled-execution)
   - Cron-like scheduler service to execute scheduled transfers
   - Jobs can be scheduled but won't run automatically yet

4. **Real S3/SMB Endpoints** (feature/real-endpoints)
   - Replace test local paths with actual S3 bucket configuration
   - Configure real SMB/CIFS shares for production use

5. **Basic Authentication** (feature/basic-auth)
   - Simple login system (even just hardcoded users initially)
   - Session management

### Clean Directory Structure
Removed empty directories: scripts, tests, data, config, database, frontend/src/utils
Current structure:
- mvp/backend/ - All backend code, worker, and database scripts
- mvp/frontend/ - React TypeScript application
- mvp/*.md - Documentation files
- mvp/docker-compose.yml - Infrastructure setup

### Current Branch Status
- On feature/initial-scaffolding branch
- Ready to merge to main - stable MVP with core transfer functionality
- Plan: Merge to main, then implement remaining features on separate branches

### Key Files Created/Modified
- `mvp/backend/worker.py` - Job processor that executes transfers
- `mvp/backend/app/services/rclone_service.py` - Updated with CLI integration, fixed --json flag issue
- `mvp/backend/app/services/throttle_controller.py` - Added can_start_transfer method
- `mvp/backend/app/models/job.py` - Added missing fields (name, schedule, etc.) and relationships
- `mvp/backend/app/schemas/*.py` - Fixed type mismatches (max_bandwidth, event rule fields)
- `mvp/backend/app/api/api_v1/endpoints/*.py` - All API endpoints
- `mvp/frontend/src/pages/Endpoints.tsx` - Full CRUD functionality
- `mvp/frontend/src/pages/Transfers.tsx` - Fixed redirect after job creation
- `mvp/frontend/src/components/CreateTransferForm.tsx` - Enhanced transfer creation
- `mvp/frontend/src/types/index.ts` - Updated Job interface with all fields
- `mvp/backend/setup_test_data.py` - Creates test files
- `mvp/backend/update_test_endpoints.py` - Configures test paths
- `mvp/manage.sh` - Service management script (June 28, 2025)

## Documentation Files (Keep Updated!)
- `mvp/README.md` - Main overview and quick start (Updated June 29 with Phase 1 next steps)
- `mvp/ARCHITECTURE.md` - System design and technology stack (Updated June 29 with 6-week plan)
- `mvp/RUNNING_SERVICES.md` - Service management guide
- `mvp/FEATURES.md` - Feature status and testing (Updated June 29 - SMB/SFTP not implemented)
- `mvp/IMPLEMENTATION_STATUS.md` - What's implemented vs missing
- `mvp/IMPLEMENTATION_PLAN.md` - Complete 6-week phased plan (Updated June 29 with revised approach)
- `mvp/REMOTE_TRANSFER_QUICKSTART.md` - Concrete steps to enable S3/SMB/SFTP
- `mvp/DISTRIBUTED_ARCHITECTURE.md` - Post-MVP distributed agent architecture
- `mvp/LOG_VIEWER_IMPLEMENTATION.md` - Log viewer UI for troubleshooting
- `mvp/MIGRATION_SUMMARY.md` - Event Rules → Transfer Templates migration guide
- `working-files/CLAUDE.md` - This memory file

## Documentation Update Process

### When to Update Documentation
1. **After implementing a new feature** - Update FEATURES.md and IMPLEMENTATION_STATUS.md
2. **After architectural changes** - Update ARCHITECTURE.md
3. **After changing services** - Update RUNNING_SERVICES.md
4. **After major milestones** - Update README.md and this file

### How to Request Documentation Update & Git Commit
Say: "Update documentation for [feature/change] and commit"

I will:
1. Update relevant documentation files
2. Update this memory file
3. Create a git commit with format:
   ```
   docs: Update documentation for [feature/change]
   
   - Updated FEATURES.md with new capability
   - Updated IMPLEMENTATION_STATUS.md progress
   - Updated README.md if needed
   
   🤖 Generated with Claude Code
   
   Co-Authored-By: Claude <noreply@anthropic.com>
   ```

### Example Commands
- "Update documentation for S3 integration and commit"
- "Update documentation for scheduler auto-start and commit"
- "Update documentation for authentication implementation and commit"

## Major Discoveries and Refactoring (June 29, 2025)

### 1. Primary Use Case Clarification
- **Discovery**: Current implementation focuses too much on local directory transfers
- **Reality**: Primary business value is in:
  - Cloud-to-on-premise transfers (S3 → SMB shares)
  - Machine-to-machine transfers (SFTP → SFTP)
  - Event-driven workflows (S3 events trigger transfers)
- **Action**: Created IMPLEMENTATION_PLAN.md and REMOTE_TRANSFER_QUICKSTART.md to refocus priorities

### 2. Event Rules → Transfer Templates Refactoring
- **Problem**: "Event Rules" terminology was confusing (manual transfers aren't events)
- **Solution**: Renamed throughout codebase to "Transfer Templates"
- **Scope**: Database migration, all models, schemas, APIs, and UI components
- **Result**: More intuitive naming that better represents the functionality

### 3. Scheduled Execution Branch Issues
- **Intent**: feature/scheduled-execution was meant to implement cron-based job execution
- **Reality**: Spent most time fixing Event Rules naming and job execution bugs
- **What Was Done**:
  - Created scheduler service and supporting code
  - Added test scripts for scheduled jobs
  - Fixed critical bugs in job execution flow
- **What Wasn't Done**:
  - UI for creating scheduled jobs
  - API endpoints for scheduled job management
  - Integration with manage.sh startup

### 4. Remote Transfer Enablement Plan
- **Phase 1**: Enable S3, SMB, SFTP endpoints (configuration only)
- **Phase 2**: S3 event integration via SQS
- **Phase 3**: Production hardening (retry logic, security)
- **Phase 4**: Advanced features (bandwidth throttling, etc.)
- **Phase 5**: Distributed Architecture (Post-MVP) - CRITICAL for production value
- **Quick Wins**: Can immediately test S3 transfers by adding AWS credentials

### 5. Distributed Architecture Requirements (June 29, 2025)
- **Discovery**: Current MVP only supports local transfers on same server as UI
- **Requirement**: Production needs single UI to control transfers between ANY servers
- **Example**: UI on Server A initiates transfer from Server B to Server C
- **Solution**: Agent-based architecture with central control plane
- **Documentation**: Created DISTRIBUTED_ARCHITECTURE.md with complete design

### 6. Log Viewer UI Requirement (June 29, 2025)
- **Need**: View transfer logs without SSH access for troubleshooting
- **Priority**: P0 - Critical for remote transfer debugging
- **Implementation**: 2-3 hours of work, no external dependencies
- **Features**: Log filtering, search, real-time tailing via WebSocket
- **Documentation**: Created LOG_VIEWER_IMPLEMENTATION.md with complete guide

## Complete 6-Week Implementation Plan (June 29, 2025)

### Phase 1: Enable Remote Transfers (Week 1)
- **Day 1-2**: S3 (30 min config) + Log Viewer (3 hours implementation)
- **Day 3-4**: SMB implementation in rclone_service.py (3 hours)
- **Day 5**: SFTP implementation in rclone_service.py (3 hours)
- **Deliverables**: S3/SMB/SFTP transfers working, log viewer UI

### Phase 2: Event-Driven Architecture (Week 2)
- S3 → SQS event integration
- Retry logic with exponential backoff
- Enable scheduler service
- Transfer chains (S3 → Primary → Archive)

### Phase 3: Production Hardening (Week 3)
- Credential encryption
- Audit logging
- Health checks
- Prometheus metrics
- Bandwidth management

### Phase 4: Advanced Features (Week 4)
- Advanced filtering
- Email/webhook notifications
- API authentication (JWT)
- Performance optimizations

### Phase 5: Distributed Architecture (Week 5-6)
- Transfer agent service
- Control plane separation
- Cross-server transfer orchestration
- Production deployment

## Current Implementation Status (June 29, 2025 - Phase 1 Day 1)

### ✅ Completed Today
1. **Created feature/phase1-remote-transfers branch**
2. **Implemented Log Viewer** (3 hours as planned):
   - Backend endpoint at `/api/v1/logs/{log_type}`
   - React UI component with filtering, search, auto-refresh
   - Syntax highlighting for log levels
   - Fixed API route registration issue (double /logs prefix)
   - Currently using absolute paths (TODO: make configurable)

### 🔧 Implementation Notes
- **Log Path Issue**: Had to use absolute path `/Users/tkitchens/projects/ctf/rclone-poc/mvp/logs/` 
  - Relative path resolution was problematic
  - TODO: Make this configurable via environment variable
- **API Route Fix**: Changed from `@router.get("/logs/{log_type}")` to `@router.get("/{log_type}")`
  - Router already has `/logs` prefix, was causing `/api/v1/logs/logs/backend`

### 📋 Remaining Phase 1 Tasks

#### Day 1-2 (Today/Tomorrow)
- [ ] Add AWS credentials to backend/.env
- [ ] Test S3 → local transfers via UI
- [ ] Verify S3 endpoint configuration works

#### Day 3-4 Tasks (SMB)
- [ ] Update `backend/app/services/rclone_service.py`
- [ ] Add SMB config in worker.py `_configure_endpoint()`
- [ ] Test with real Windows shares

#### Day 5 Tasks (SFTP)
- [ ] Update `backend/app/services/rclone_service.py`
- [ ] Add SFTP config in worker.py `_configure_endpoint()`
- [ ] Support both password and key auth

## Key Decisions Made

1. **Continue MVP Approach** - Get remote transfers working first (1 week)
2. **Defer Distributed Architecture** - Implement in weeks 5-6 after core features work
3. **Prioritize Business Value** - S3 transfers can work in 30 minutes with credentials
4. **Fix Implementation Gaps** - SMB/SFTP need 6 hours total implementation
5. **Add Critical Tools** - Log viewer essential for debugging remote transfers