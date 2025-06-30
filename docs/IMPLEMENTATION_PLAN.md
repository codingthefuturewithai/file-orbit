# CTF Rclone POC - Complete Implementation Plan (Revised)

## Executive Summary

Focus on enabling **machine-to-machine** and **cloud-to-on-premise** transfers with minimal rework. Start with MVP enhancements, then evolve to distributed architecture.

## Current Status (June 29, 2025)

### What Works
- ✅ Local directory → Local directory transfers
- ✅ Manual transfer creation via UI
- ✅ Event-driven transfers for local file watching
- ✅ Transfer Templates (formerly Event Rules) fully refactored
- ✅ Job execution fixed (was stuck in queued status)

### What Doesn't Work (Required for Production)
- ❌ S3 transfers - Code exists but needs AWS credentials
- ❌ SMB/CIFS transfers - UI exists but rclone config not implemented
- ❌ SFTP transfers - UI exists but rclone config not implemented
- ❌ S3 event monitoring - SQS integration not configured
- ❌ Distributed architecture - Cannot control transfers between servers

## Phase 1: Enable Remote Transfers (Week 1)

### Completed Items
1. **S3 Integration** ✅ COMPLETED (Dec 6, 2024)
   - Added AWS credentials to .env file
   - Fixed critical bugs:
     - Enum type handling (EndpointType.S3 → endpoint.type.value)
     - S3 path construction (now includes bucket name)
     - IAM permissions (added s3:ListAllMyBuckets)
   - Successfully tested S3 → local transfers
   - Added transfer edit feature for quick fixes

2. **Log Viewer UI** ✅ COMPLETED (June 30, 2025)
   - Backend API endpoint implemented
   - Frontend shows logs for all services
   - Filtering and auto-refresh working
   - Fixed hardcoded username path issue

3. **Path Template Substitution** ✅ COMPLETED (June 30, 2025)
   - Fixed template variables not being replaced
   - Supports {year}, {month}, {day}, {filename}, {timestamp}
   - Resolved files being created as directories

### Next Priority (Revised June 30, 2025)
**USER DECISION**: Prioritize SMB/SFTP over log path configuration

### Day 1-2: SMB/SFTP Implementation
1. **SMB/CIFS Support** (3 hours) - NEXT PRIORITY
   ```python
   # Update rclone_service.py
   elif endpoint.type == 'smb':
       config.update({
           'type': 'smb',
           'host': endpoint.config.get('host'),
           'user': endpoint.config.get('user'),
           'pass': endpoint.config.get('password'),
           'domain': endpoint.config.get('domain', 'WORKGROUP'),
           'share': endpoint.config.get('share')
       })
   ```
   - Test with actual Windows shares
   - Handle domain\username format
   - Verify UNC path support

### Day 5: SFTP Implementation  
4. **SFTP Support** (3 hours)
   ```python
   # Update rclone_service.py
   elif endpoint.type == 'sftp':
       config.update({
           'type': 'sftp',
           'host': endpoint.config.get('host'),
           'user': endpoint.config.get('user'),
           'pass': endpoint.config.get('password'),
           'key_file': endpoint.config.get('key_file'),
           'port': endpoint.config.get('port', 22),
           'use_insecure_cipher': False
       })
   ```
   - Support both password and key auth
   - Test with real SFTP servers

5. **Endpoint Connectivity Testing** (2 hours)
   ```python
   @router.post("/api/v1/endpoints/test")
   async def test_endpoint_connection(endpoint: EndpointCreate):
       # Test connection before saving
       # Return specific error messages
   ```

## Phase 1 Deliverables
- ✅ S3 → Local transfers working
- ✅ S3 → SMB transfers working  
- ✅ SFTP → Local transfers working
- ✅ Cross-protocol transfers (SFTP → S3)
- ✅ Log viewer for troubleshooting

## Phase 2: Event-Driven Architecture (Week 2)

### Day 1-2: S3 Event Integration
1. **SQS Configuration** (4 hours)
   ```python
   # S3 bucket → SNS → SQS setup
   SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/xxx/ctf-s3-events
   
   # Update s3_event_monitor.py
   - Poll SQS for S3 events
   - Parse event notifications
   - Trigger transfers automatically
   ```

2. **Event Processing Pipeline** (4 hours)
   ```python
   # Robust event handling
   - Event deduplication (Redis-based)
   - Dead letter queue for failures
   - Event replay capability
   - Audit trail in database
   ```

### Day 3-4: Production Features
3. **Retry Logic** (3 hours)
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential
   
   @retry(
       stop=stop_after_attempt(3),
       wait=wait_exponential(min=1, max=60),
       retry=retry_if_exception_type(NetworkError)
   )
   async def execute_transfer(job):
       # Automatic retry with exponential backoff
   ```

4. **Scheduler Integration** (2 hours)
   ```bash
   # Enable existing scheduler service
   - Update manage.sh to start scheduler
   - Test scheduled transfers
   - Add UI for viewing schedules
   ```

5. **Transfer Chains** (3 hours)
   ```python
   # Multi-destination transfers
   - S3 → Primary Storage → Archive
   - Configure in Transfer Templates
   - Track chain progress
   ```

## Phase 2 Deliverables
- ✅ Automatic S3 event-driven transfers
- ✅ Scheduled transfers running automatically
- ✅ Network failure recovery
- ✅ Transfer chains working

## Phase 3: Production Hardening (Week 3)

### Security & Compliance
1. **Credential Encryption** (4 hours)
   ```python
   # Use cryptography library
   - Encrypt credentials at rest
   - Key rotation support
   - Environment-based master key
   ```

2. **Audit Logging** (3 hours)
   ```python
   # Comprehensive audit trail
   - Who initiated transfers
   - Source/destination details
   - Success/failure reasons
   - Compliance reporting
   ```

### Monitoring & Operations
3. **Health Checks** (2 hours)
   ```python
   @router.get("/health")
   async def health_check():
       return {
           "database": check_db(),
           "redis": check_redis(),
           "rclone": check_rclone(),
           "disk_space": check_disk()
       }
   ```

3.5. **Log File Management** (3 hours) - CRITICAL GAP
   ```python
   # Current: Hardcoded project paths
   # Required: System-standard locations
   
   # 1. Make log paths configurable
   LOG_DIR = os.getenv('FILE_ORBIT_LOG_DIR', '/var/log/file-orbit')
   
   # 2. Create log directory structure
   /var/log/file-orbit/
   ├── backend.log
   ├── worker.log
   ├── event-monitor.log
   └── scheduler.log
   
   # 3. Configure log rotation
   # 4. Update manage.sh for proper log handling
   # 5. Update all services to use configured paths
   ```

4. **Metrics Collection** (3 hours)
   ```python
   # Prometheus metrics
   - Transfer success/failure rates
   - Average transfer duration
   - Queue depth
   - Active transfers by endpoint
   ```

5. **Bandwidth Management** (4 hours)
   ```python
   # Per-endpoint throttling
   - Implement in throttle_controller.py
   - Dynamic adjustment based on time
   - Priority queues for transfers
   ```

## Phase 3 Deliverables
- ✅ Encrypted credential storage
- ✅ Complete audit trail
- ✅ Production monitoring
- ✅ Bandwidth throttling

## Phase 4: Advanced Features (Week 4)

1. **Advanced Filtering** (4 hours)
   - Include/exclude patterns
   - File age filters
   - Size-based filtering
   - Metadata matching

2. **Notifications** (3 hours)
   - Email on failure/success
   - Webhook integration
   - Slack/Teams alerts

3. **API Authentication** (4 hours)
   - JWT token support
   - API key management
   - Rate limiting

4. **Performance Optimization** (3 hours)
   - Connection pooling
   - Parallel transfers
   - Chunked uploads for large files

## Phase 4 Deliverables
- ✅ Enterprise-ready features
- ✅ Full API security
- ✅ Advanced filtering options

## Phase 5: Distributed Architecture (Week 5-6)

### Week 5: Agent Development
1. **Transfer Agent Service** (1 week)
   ```python
   class TransferAgent:
       def __init__(self, agent_id: str, control_plane_url: str):
           self.agent_id = agent_id
           self.control_plane = control_plane_url
           self.rclone = RcloneService()
           
       async def register(self):
           # Register with control plane
           # Report capabilities
           # Start heartbeat
           
       async def execute_remote_transfer(self, job):
           # Receive job from control plane
           # Execute locally
           # Report progress back
   ```

2. **Control Plane Separation**
   ```python
   # Extract from current worker
   - Job routing logic
   - Agent management
   - Progress aggregation
   - Security tokens
   ```

### Week 6: Production Deployment
3. **Agent Deployment**
   - Ansible playbooks
   - Docker containers
   - Auto-registration
   - Health monitoring

4. **Network Architecture**
   - Service discovery
   - Load balancing
   - Failover support
   - Cross-region support

## Phase 5 Deliverables
- ✅ Agents deployed on all servers
- ✅ Central UI controls any transfer
- ✅ Full distributed architecture
- ✅ Production deployment ready

## Success Metrics by Phase

| Phase | Success Criteria | Business Value |
|-------|-----------------|----------------|
| 1 | S3/SMB/SFTP transfers working | Core functionality enabled |
| 2 | Event-driven S3 transfers | Automation achieved |
| 3 | 99.9% transfer success rate | Production ready |
| 4 | Full API, advanced features | Enterprise ready |
| 5 | UI on A controls B→C transfers | Full distributed capability |

## Risk Mitigation

1. **Each phase delivers value** - Can stop at any phase
2. **Backwards compatible** - Current code remains useful
3. **Incremental complexity** - Simple features first
4. **Early validation** - Test with real endpoints ASAP

## Total Timeline
- **Phase 1**: 1 week (Remote transfers working)
- **Phase 2**: 1 week (Event-driven automation)
- **Phase 3**: 1 week (Production hardening)
- **Phase 4**: 1 week (Advanced features)
- **Phase 5**: 2 weeks (Distributed architecture)

**Total**: 6 weeks to full production distributed system

**Minimum Viable Production**: 3 weeks (Phases 1-3)

## Immediate Next Steps (For Session Resumption)

### 1. Create feature branch for Phase 1
```bash
git checkout -b feature/phase1-remote-transfers
```

### 2. Day 1 Tasks (S3 & Log Viewer)
- [ ] Add AWS credentials to `.env` and test S3 transfers
- [ ] Implement log viewer backend endpoint
- [ ] Create log viewer UI component
- [ ] Test S3 → local transfer

### 3. Day 3-4 Tasks (SMB Implementation)
- [ ] Update `rclone_service.py` with SMB config
- [ ] Test with Windows shares
- [ ] Handle authentication edge cases

### 4. Day 5 Tasks (SFTP Implementation)
- [ ] Update `rclone_service.py` with SFTP config
- [ ] Support both password and key auth
- [ ] Test with real SFTP servers

## Branch Strategy

1. **Current**: `feature/scheduled-execution` (ready to merge)
2. **Next**: `feature/phase1-remote-transfers` (Week 1)
3. **Then**: `feature/phase2-event-driven` (Week 2)
4. **Then**: `feature/phase3-production` (Week 3)
5. **Then**: `feature/phase4-advanced` (Week 4)
6. **Finally**: `feature/phase5-distributed` (Week 5-6)