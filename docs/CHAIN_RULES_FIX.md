# Chain Rules Implementation Fix

## Overview
Chain rules allow a single file transfer to automatically trigger additional transfers to multiple destinations. This feature is currently broken for batch/manual transfers due to an architectural issue with how chain jobs are created.

## User Intent & Use Cases

### Primary Use Case
As a user, I want to:
1. Transfer files from a source to a primary destination
2. Have those files automatically copied to one or more secondary destinations
3. This should work whether I'm transferring 1 file or 100 files

### Example Scenarios

#### Scenario 1: Video Production Workflow
- New video files arrive in watch folder
- Primary transfer: Watch folder → Production SMB share
- Chain 1: Production SMB → Backup NAS
- Chain 2: Production SMB → Cloud archive (S3)

#### Scenario 2: Document Distribution
- Documents uploaded to SFTP
- Primary transfer: SFTP → Internal file server
- Chain 1: Internal server → Department A share
- Chain 2: Internal server → Department B share
- Chain 3: Internal server → Offsite backup

#### Scenario 3: Media Processing Pipeline
- Raw media files in local directory
- Primary transfer: Local → Processing server
- Chain 1: Processing server → Archive
- Chain 2: Processing server → CDN origin

## Current Implementation & Limitations

### What Works
- Chain rules work correctly for **single file transfers** triggered by events
- Example: One file appears in watch folder → triggers template → chains execute properly

### What's Broken
- Chain rules fail for **batch transfers** (multiple files)
- Chain rules fail for **manual template execution** with wildcards
- Chain rules fail when using **path templates** with variables like `{original_filename}`

### Root Cause
The system creates chain jobs immediately when the parent job is created, using the template path (e.g., `destination/{original_filename}`). For batch transfers, this unresolved template path is meaningless, causing chain jobs to fail when they try to access `{original_filename}` as a literal directory name.

## Technical Details

### Current Flow (Broken)
```
1. User executes template manually
2. System creates parent job with template path: "smb-share/{original_filename}"
3. System IMMEDIATELY creates chain jobs with source: "smb-share/{original_filename}"
4. Parent job executes, transferring files:
   - video1.mp4 → smb-share/video1.mp4
   - video2.mp4 → smb-share/video2.mp4
5. Chain job tries to list files from "smb-share/{original_filename}" (literal)
6. FAILS: No such directory
```

### Correct Flow (Proposed)
```
1. User executes template manually
2. System creates parent job with template path
3. Parent job executes, transferring files:
   - video1.mp4 → smb-share/video1.mp4 ✓
   - Creates chain job specifically for video1.mp4
   - video2.mp4 → smb-share/video2.mp4 ✓
   - Creates chain job specifically for video2.mp4
4. Each chain job has the ACTUAL resolved path
5. Chain jobs execute successfully
```

## Required Fix

### High-Level Changes
1. **Delay chain job creation** until after each file transfers successfully
2. **Create individual chain jobs** for each transferred file (not one job for the batch)
3. **Store actual destination paths** for each transferred file
4. **Pass resolved paths** to chain jobs, not template paths

### Implementation Approach

#### Option 1: Per-File Chain Jobs (Recommended)
- After each file transfers successfully, create its chain jobs
- Each chain job handles one specific file
- Maintains 1:1 relationship between files and their chains

#### Option 2: Batch Chain Jobs with File List
- After all files transfer, create one chain job with a list of actual file paths
- More complex but potentially more efficient for large batches

### Code Locations to Modify
1. `worker.py` - `_execute_transfer()` method
   - After successful transfer, create chain jobs with actual paths
   
2. `app/services/chain_job_service.py`
   - Modify to accept actual file paths instead of template paths
   
3. `app/models/job.py`
   - May need to store actual transferred file information

## Acceptance Criteria

1. **Single File Transfers**
   - Chain rules continue to work as they do now
   
2. **Batch Transfers**
   - When transferring multiple files, each file flows through the entire chain
   - Each file's chain jobs use the actual resolved destination path
   
3. **Manual Execution**
   - Re-executing a template with chain rules works for all matching files
   - No template variables in chain job paths
   
4. **Event-Driven Transfers**
   - Continue to work as expected
   - Performance should not degrade

5. **Error Handling**
   - If a file's primary transfer fails, no chain jobs are created for that file
   - If a chain transfer fails, it doesn't affect other files' chains
   - Clear error messages indicating which file in which chain failed

## Testing Scenarios

### Test 1: Manual Batch Transfer
1. Create template: Local → SMB with pattern `*.mp4`
2. Add chain rule: SMB → Local backup folder
3. Place 5 MP4 files in source
4. Execute template manually
5. Verify: All 5 files appear in both SMB and backup folder

### Test 2: Event-Driven Single File
1. Create template watching for new files
2. Add 2 chain rules to different destinations
3. Drop one file in watch folder
4. Verify: File appears in all 3 destinations

### Test 3: Mixed File Types
1. Create template with pattern `*.*`
2. Add chain rule
3. Transfer mix of file types and sizes
4. Verify: Each file completes its chain regardless of type/size

### Test 4: Error Recovery
1. Create template with chain rule
2. Make chain destination unavailable
3. Execute transfer
4. Verify: Primary transfer succeeds, chain fails gracefully
5. Fix destination, retry chains

## User Experience Impact

### Before Fix
- "Chain rules only work sometimes"
- "I have to manually copy files to secondary locations"
- "Template execution fails mysteriously"

### After Fix
- Chain rules work consistently for all transfer types
- No manual intervention needed
- Clear visibility into each file's journey through the chain

## Priority & Effort

**Priority:** High - Core feature is broken for common use cases

**Effort:** Medium - Requires refactoring job creation flow but doesn't need UI changes

**Risk:** Medium - Need careful testing to ensure existing event-driven chains still work

## Alternative Solutions

### Short Term
- Document that chain rules only work for single-file transfers
- Disable chain rules UI for manual transfer templates
- Add warning when creating chain rules with path templates

### Long Term
- Implement proper per-file chain job creation as described above
- Add UI to show chain progression for each file
- Consider adding parallel chain execution option