# PBS Rclone MVP Architecture

## Overview

The PBS Rclone MVP is a distributed file transfer orchestration system designed for **machine-to-machine** and **cloud-to-on-premise** transfers. It provides enterprise features like event-driven transfers, scheduling, and monitoring while leveraging rclone's extensive protocol support.

**CURRENT STATUS**: MVP only supports local transfers. Production use requires implementation of remote endpoints (S3, SMB, SFTP) and distributed architecture.

## Primary Use Cases

1. **Cloud-to-On-Premise Event-Driven Transfers**
   - S3 → On-premise SMB shares
   - S3 → Local storage servers
   - Triggered by S3 events via SQS/SNS

2. **Cross-Machine Transfers**
   - SFTP server → SFTP server
   - SMB share → SMB share
   - Cross-protocol (SFTP → SMB)

3. **On-Premise-to-Cloud Backup**
   - Local files → S3
   - Network shares → Cloud storage
   - Scheduled and event-driven

## System Architecture

**Note**: This architecture currently supports LOCAL transfers only. See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the 6-week plan to enable remote transfers and distributed architecture.

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   React UI  │────▶│ FastAPI     │────▶│  PostgreSQL  │
│  (Port 3000)│     │  Backend    │     │  Database    │
└─────────────┘     │ (Port 8000) │     └──────────────┘
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    Redis    │
                    │  Job Queue  │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼──────┐  ┌────────▼──────┐  ┌───────▼────────┐
│   Worker     │  │ Event Monitor │  │   Scheduler    │
│   Service    │  │   Service     │  │   Service      │
└───────┬──────┘  └───────┬───────┘  └────────────────┘
        │                  │
┌───────▼──────┐          │
│   Rclone     │          │
│     CLI      │          │
└──────────────┘          │
                          │
                   ┌──────▼──────┐
                   │  AWS SQS    │
                   │ S3 Events   │
                   └─────────────┘
```

## Services Breakdown

### Infrastructure Services (Docker)

| Service | Purpose | Port | Container Name |
|---------|---------|------|----------------|
| PostgreSQL | Primary database | 5432 | pbs-rclone-postgres |
| Redis | Job queue & caching | 6379 | pbs-rclone-redis |
| Rclone RC | Remote control API (unused) | 5572 | pbs-rclone-rc |

### Application Services (Python/Node)

| Service | Purpose | Technology | Default Port |
|---------|---------|------------|--------------|
| Backend API | REST API & business logic | FastAPI (Python) | 8000 |
| Frontend | Web interface | React (TypeScript) | 3000 |
| Worker | Job processor | Python | N/A |
| Event Monitor | File/S3 event watcher | Python | N/A |
| Scheduler | Cron job executor | Python | N/A |

## Data Flow

### Manual Transfer
1. User creates transfer in UI
2. Frontend calls POST /api/v1/jobs
3. Backend creates job in PostgreSQL
4. Backend queues job ID in Redis
5. Worker picks up job from Redis
6. Worker executes rclone CLI command
7. Worker updates job status in PostgreSQL

### Event-Driven Transfer (Local)
1. File appears in watched directory
2. Event Monitor detects change (using watchdog)
3. Event Monitor matches against transfer templates
4. Creates job and queues in Redis
5. Same flow as manual transfer from step 5

### Event-Driven Transfer (S3)
1. File uploaded to S3 bucket
2. S3 sends event to SQS queue
3. Event Monitor polls SQS for messages
4. Parses S3 event and matches transfer templates
5. Creates job with S3 source and on-premise destination
6. Same flow as manual transfer from step 5

### Scheduled Transfer
1. Scheduler service runs every minute
2. Checks for jobs due to run (cron expression)
3. Queues due jobs in Redis
4. Same flow as manual transfer from step 5

## Technology Stack

### Backend
- **Language**: Python 3.11
- **Framework**: FastAPI
- **ORM**: SQLAlchemy (async)
- **Queue**: Redis with custom manager
- **File Monitoring**: watchdog
- **Scheduling**: croniter
- **AWS Integration**: aioboto3 (for future S3)

### Frontend
- **Language**: TypeScript
- **Framework**: React 18
- **UI Library**: Tailwind CSS
- **HTTP Client**: Axios
- **Icons**: Heroicons

### Infrastructure
- **Database**: PostgreSQL 15
- **Cache/Queue**: Redis 7
- **File Transfer**: Rclone (CLI, not RC API)
- **Container Runtime**: Docker

## Key Design Decisions

1. **Rclone CLI over RC API**: More stable and feature-complete
2. **Redis for Queue**: Simple, fast, reliable for job queuing
3. **Separate Services**: Modular design allows independent scaling
4. **Event-Driven Architecture**: Supports S3/SQS events and local file watching
5. **Protocol Agnostic**: Same interface for S3, SMB, SFTP, local
6. **Safe File Transfers**: Default rclone behavior with .partial files
7. **Optional Checksums**: Per-transfer integrity verification
8. **Distributed First**: Designed for cross-machine transfers

## Security Considerations

### Current State
- No authentication implemented (MVP limitation)
- Database credentials in environment variables
- Rclone RC API running without auth (not used)
- File system access based on process permissions
- **S3/SMB/SFTP endpoints NOT working** - Implementation required (see Phase 1 of plan)
- **No log viewer UI** - Cannot debug without SSH access

### Required for Production
- **Credential Management**: AWS KMS or HashiCorp Vault
- **Network Security**: VPN/Direct Connect for cloud transfers
- **Audit Logging**: All transfer activities logged
- **Access Control**: Role-based permissions
- **Encryption**: TLS for all network transfers

## Implementation Phases (6-Week Plan)

### Phase 1: Enable Remote Transfers (Week 1)
- Add S3 credentials and test transfers (30 min)
- Implement SMB/SFTP rclone config (6 hours)
- Create log viewer UI (3 hours)
- Add endpoint connectivity testing

### Phase 2: Event-Driven Architecture (Week 2)
- Configure S3 → SQS event pipeline
- Add retry logic with exponential backoff
- Enable scheduler service
- Implement transfer chains

### Phase 3: Production Hardening (Week 3)
- Encrypt credentials at rest
- Add comprehensive audit logging
- Implement health checks
- Add Prometheus metrics

### Phase 4: Advanced Features (Week 4)
- Advanced filtering and transformations
- Email/webhook notifications
- API authentication (JWT)
- Performance optimizations

### Phase 5: Distributed Architecture (Week 5-6)
- Implement transfer agents
- Separate control plane
- Enable cross-server transfers
- Production deployment

## Post-MVP: Distributed Architecture Required

**CRITICAL**: The current MVP architecture only supports transfers on the local server. Production requires a distributed architecture where:

- Single UI can control transfers between ANY servers
- Central control plane orchestrates distributed agents
- Example: UI on Server A initiates transfer from Server B to Server C

See [DISTRIBUTED_ARCHITECTURE.md](DISTRIBUTED_ARCHITECTURE.md) for complete design.

## File Transfer Safety Features

### Temporary File Handling
- **Default Behavior**: Rclone uploads to temporary files with `.partial` suffix
- **Atomic Operations**: Files renamed to final name only after successful transfer
- **Configurable**: Custom temp directory via `--temp-dir` flag
- **Benefits**: Prevents downstream systems from processing incomplete files

### Checksum Verification
- **Optional Feature**: Enabled per-transfer with `--checksum` flag
- **Hash Comparison**: Validates source and destination file integrity
- **Algorithm Support**: MD5, SHA1, and other hashes based on storage backend
- **Error Detection**: Identifies corruption during transfer
- **Performance Impact**: Slower transfers but guarantees data integrity

### Implementation in RcloneService
```python
# Example flags for safe transfer with checksums
flags = [
    "copy",
    source_path,
    dest_path,
    "--progress",
    "--stats", "1s",
    "--checksum",  # Enable checksum verification
    # Note: --inplace NOT used to ensure temporary files
]
```