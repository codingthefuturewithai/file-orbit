#!/usr/bin/env python3
"""
Background worker for processing file transfer jobs.
This worker polls Redis for queued jobs and executes them using rclone.
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path
from datetime import datetime, timezone
import json
import uuid

# Add parent directory to path so we can import our app
sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.services.redis_manager import redis_manager
from app.services.rclone_service import RcloneService
from app.services.throttle_controller import ThrottleController
from app.models.job import Job, JobStatus, JobType
from app.models.transfer import Transfer, TransferStatus
from app.models.endpoint import Endpoint
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JobProcessor:
    def __init__(self):
        self.running = False
        self.rclone_service = RcloneService()
        self.throttle_controller = ThrottleController()
        self.current_transfers = {}
        
    async def start(self):
        """Start the worker process"""
        self.running = True
        logger.info("Job processor started")
        
        # Connect to Redis
        await redis_manager.connect()
        
        # Load throttle limits
        await self.throttle_controller.load_endpoint_limits()
        
        # Start processing loop
        while self.running:
            try:
                await self.process_next_job()
                await asyncio.sleep(1)  # Small delay between polls
            except Exception as e:
                logger.error(f"Error in processing loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # Longer delay on error
    
    async def stop(self):
        """Stop the worker process"""
        self.running = False
        logger.info("Job processor stopping...")
        
        # Cancel any running transfers
        for transfer_id, task in self.current_transfers.items():
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled transfer {transfer_id}")
        
        await redis_manager.disconnect()
        logger.info("Job processor stopped")
    
    async def process_next_job(self):
        """Get and process the next job from the queue"""
        job_id = await redis_manager.dequeue_job()
        if not job_id:
            return
        
        logger.info(f"Processing job {job_id}")
        
        job = None  # Initialize job variable
        async with AsyncSessionLocal() as db:
            try:
                # Get job with endpoints loaded
                result = await db.execute(
                    select(Job)
                    .options(
                        selectinload(Job.source_endpoint),
                        selectinload(Job.destination_endpoint)
                    )
                    .where(Job.id == job_id)
                )
                job = result.scalar_one_or_none()
                
                if not job:
                    logger.error(f"Job {job_id} not found")
                    return
                
                # Update job status to running
                job.status = JobStatus.RUNNING
                job.started_at = datetime.now(timezone.utc)
                job.last_run_at = datetime.now(timezone.utc)
                await db.commit()
                
                # Execute the transfer
                await self.execute_job(db, job)
                
            except Exception as e:
                logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
                if job:
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.now(timezone.utc)
                    job.failed_runs += 1
                    await db.commit()
    
    async def execute_job(self, db, job: Job):
        """Execute a job by creating and running transfers"""
        try:
            # PHASE 1: Log job configuration for tracking
            logger.info(f"[FILE_TRACKING] Starting job {job.id}:")
            logger.info(f"[FILE_TRACKING]   Type: {job.type}")
            logger.info(f"[FILE_TRACKING]   Source: {job.source_endpoint.name} ({job.source_endpoint.type.value})")
            logger.info(f"[FILE_TRACKING]   Source path: {job.source_path}")
            logger.info(f"[FILE_TRACKING]   File pattern: {job.file_pattern}")
            logger.info(f"[FILE_TRACKING]   Destination: {job.destination_endpoint.name} ({job.destination_endpoint.type.value})")
            logger.info(f"[FILE_TRACKING]   Destination path: {job.destination_path}")
            logger.info(f"[FILE_TRACKING]   Parent job ID: {job.parent_job_id}")
            if job.config:
                logger.info(f"[FILE_TRACKING]   Config: {json.dumps(job.config, indent=2)}")
            # Check throttling
            can_proceed = await self.throttle_controller.can_start_transfer(
                job.source_endpoint_id,
                job.destination_endpoint_id
            )
            
            if not can_proceed:
                logger.info(f"Job {job.id} throttled, requeueing")
                job.status = JobStatus.QUEUED
                await db.commit()
                await redis_manager.enqueue_job(job.id, delay=60)  # Retry in 1 minute
                return
            
            # Get list of files to transfer
            files = await self._get_files_to_transfer(job)
            
            if not files:
                logger.warning(f"No files found for job {job.id}")
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now(timezone.utc)
                job.successful_runs += 1
                job.total_runs += 1
                await db.commit()
                return
            
            # PHASE 1: Log file discovery for tracking
            logger.info(f"[FILE_TRACKING] Job {job.id} - Found {len(files)} files to transfer:")
            for idx, file_info in enumerate(files):
                logger.info(f"[FILE_TRACKING]   [{idx+1}/{len(files)}] {file_info['name']} (size: {file_info['size']} bytes, path: {file_info['path']})")
            
            # Create transfer records
            transfers = []
            total_size = 0
            for file_info in files:
                transfer = Transfer(
                    id=str(uuid.uuid4()),
                    job_id=job.id,
                    file_name=file_info['name'],
                    file_path=file_info['path'],
                    file_size=file_info['size'],
                    status=TransferStatus.PENDING
                )
                db.add(transfer)
                transfers.append(transfer)
                total_size += file_info['size']
            
            # Update job with total files and bytes
            job.total_files = len(files)
            job.total_bytes = total_size
            
            await db.commit()
            
            # Execute transfers
            success_count = 0
            transferred_size = 0
            successful_transfers = []  # PHASE 1: Track successful transfers
            failed_transfers = []      # PHASE 1: Track failed transfers
            
            for transfer in transfers:
                try:
                    await self._execute_transfer(db, job, transfer)
                    success_count += 1
                    transferred_size += transfer.file_size
                    
                    # PHASE 1: Track successful transfer
                    successful_transfers.append({
                        'file_name': transfer.file_name,
                        'source_path': transfer.file_path,
                        'destination_path': transfer.destination_path,
                        'size': transfer.file_size,
                        'transfer_id': transfer.id  # PHASE 3: Add transfer ID for chain creation
                    })
                    logger.info(f"[FILE_TRACKING] Transfer SUCCESS: {transfer.file_name} -> {transfer.destination_path}")
                    
                    # Update job progress
                    job.transferred_files = success_count
                    job.transferred_bytes = transferred_size
                    job.progress_percentage = int((success_count / len(transfers)) * 100)
                    await db.commit()
                except Exception as e:
                    logger.error(f"Transfer {transfer.id} failed: {e}")
                    transfer.status = TransferStatus.FAILED
                    transfer.error_message = str(e)
                    await db.commit()
                    
                    # PHASE 1: Track failed transfer
                    failed_transfers.append({
                        'file_name': transfer.file_name,
                        'source_path': transfer.file_path,
                        'destination_path': transfer.destination_path,
                        'error': str(e)
                    })
                    logger.error(f"[FILE_TRACKING] Transfer FAILED: {transfer.file_name} - Error: {e}")
            
            # PHASE 1: Log job summary for tracking
            logger.info(f"[FILE_TRACKING] Job {job.id} Summary:")
            logger.info(f"[FILE_TRACKING]   Total files: {len(transfers)}")
            logger.info(f"[FILE_TRACKING]   Successful: {len(successful_transfers)}")
            logger.info(f"[FILE_TRACKING]   Failed: {len(failed_transfers)}")
            if successful_transfers:
                logger.info("[FILE_TRACKING]   Successful transfers:")
                for idx, transfer in enumerate(successful_transfers):
                    logger.info(f"[FILE_TRACKING]     [{idx+1}] {transfer['file_name']} -> {transfer['destination_path']}")
            
            # Update job status
            if success_count == len(transfers):
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now(timezone.utc)
                job.successful_runs += 1
                
                # Check for chain jobs - pass successful transfers for future use
                await self._process_chain_jobs(db, job, successful_transfers)
            else:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now(timezone.utc)
                job.failed_runs += 1
            
            job.total_runs += 1
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error executing job {job.id}: {e}", exc_info=True)
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            job.failed_runs += 1
            job.total_runs += 1
            await db.commit()
    
    async def _get_files_to_transfer(self, job: Job) -> list:
        """Get list of files to transfer based on job configuration"""
        try:
            # Configure source endpoint
            source_config = await self._configure_endpoint(job.source_endpoint, "source")
            
            # For chain jobs with specific file paths, handle differently
            if job.type == JobType.CHAINED and job.source_path and not job.file_pattern:
                # This is a chain job for a specific file
                # Extract directory and filename
                import os
                dir_path = os.path.dirname(job.source_path)
                file_name = os.path.basename(job.source_path)
                
                # If there's no directory part, use empty string for dir_path
                if not dir_path:
                    dir_path = ""
                
                # List files in the directory and filter for the specific file
                files = await self.rclone_service.list_files(
                    remote_name="source",
                    path=dir_path,
                    pattern=file_name  # Use the specific filename as pattern
                )
            else:
                # Normal job - list files from source
                files = await self.rclone_service.list_files(
                    remote_name="source",
                    path=job.source_path,
                    pattern=job.file_pattern or "*"
                )
            
            return files
        except Exception as e:
            logger.error(f"Error listing files for job {job.id}: {e}")
            raise
    
    async def _configure_endpoint(self, endpoint: Endpoint, name: str) -> dict:
        """Configure rclone remote for an endpoint"""
        config = {
            'name': name,
            'type': endpoint.type.value  # Get the string value from the enum
        }
        
        # Map endpoint config to rclone config
        if endpoint.type.value == 'local':
            # Local needs the base path
            config['path'] = endpoint.config.get('path', '/')
        elif endpoint.type.value == 's3':
            # Use endpoint credentials if provided, otherwise fall back to environment variables
            access_key = endpoint.config.get('access_key') or settings.AWS_ACCESS_KEY_ID
            secret_key = endpoint.config.get('secret_key') or settings.AWS_SECRET_ACCESS_KEY
            region = endpoint.config.get('region') or settings.AWS_REGION
            
            config.update({
                'provider': 'AWS',
                'access_key_id': access_key,
                'secret_access_key': secret_key,
                'region': region,
                'bucket': endpoint.config.get('bucket')
            })
        elif endpoint.type.value == 'smb':
            config.update({
                'host': endpoint.config.get('host'),
                'user': endpoint.config.get('user'),
                'password': endpoint.config.get('password'),
                'domain': endpoint.config.get('domain', 'WORKGROUP'),
                'share': endpoint.config.get('share')  # This was missing!
            })
        elif endpoint.type.value == 'sftp':
            sftp_config = {
                'host': endpoint.config.get('host'),
                'user': endpoint.config.get('user'),
                'port': endpoint.config.get('port', 22)
            }
            
            # Handle authentication - either key-based or password
            if endpoint.config.get('key_file'):
                sftp_config['key_file'] = endpoint.config.get('key_file')
                if endpoint.config.get('key_passphrase'):
                    sftp_config['key_passphrase'] = endpoint.config.get('key_passphrase')
            else:
                sftp_config['pass'] = endpoint.config.get('password')
            
            # Add known hosts file if specified
            if endpoint.config.get('known_hosts_file'):
                sftp_config['known_hosts_file'] = endpoint.config.get('known_hosts_file')
                
            config.update(sftp_config)
        
        # Configure the remote
        await self.rclone_service.configure_remote(name, config)
        return config
    
    async def _execute_transfer(self, db, job: Job, transfer: Transfer):
        """Execute a single file transfer"""
        transfer.status = TransferStatus.IN_PROGRESS
        transfer.started_at = datetime.now(timezone.utc)
        await db.commit()
        
        try:
            # Configure endpoints
            await self._configure_endpoint(job.source_endpoint, "source")
            await self._configure_endpoint(job.destination_endpoint, "dest")
            
            # Build source and destination paths
            source_path = self._build_remote_path("source", job.source_endpoint, job.source_path, transfer.file_path)
            
            # PHASE 1: Log source path building
            logger.info(f"[FILE_TRACKING] Source path: endpoint_type={job.source_endpoint.type.value}, base={job.source_path}, file={transfer.file_path} -> {source_path}")
            
            # For destination, apply template substitution if the path contains template variables
            dest_base_path = job.destination_path
            original_dest_path = dest_base_path  # PHASE 1: Track original template
            
            if any(var in dest_base_path for var in ['{year}', '{month}', '{day}', '{filename}', '{original_filename}', '{timestamp}']):
                # Apply template substitution
                substituted_path = self._apply_path_template(dest_base_path, transfer.file_name)
                # Extract the directory path (remove the filename if it's at the end)
                from pathlib import Path
                path_obj = Path(substituted_path)
                if path_obj.name == transfer.file_name:
                    # If the path ends with the filename, use the parent directory
                    dest_base_path = str(path_obj.parent)
                else:
                    # Otherwise use the full substituted path
                    dest_base_path = substituted_path
                
                # PHASE 1: Log destination path template processing
                logger.info(f"[FILE_TRACKING] Destination template: '{original_dest_path}' -> '{dest_base_path}'")
            
            # Build the final destination path
            dest_path = self._build_remote_path("dest", job.destination_endpoint, dest_base_path, "")
            
            # PHASE 1: Track the actual destination path for each file
            # This includes the full path with filename after template substitution
            actual_dest_file_path = f"{dest_path}/{transfer.file_name}"
            transfer.destination_path = actual_dest_file_path
            logger.info(f"[FILE_TRACKING] Transfer {transfer.id} - File: {transfer.file_name}, Destination: {actual_dest_file_path}")
            await db.commit()
            
            # Track this transfer
            transfer_task = asyncio.create_task(
                self._run_transfer_with_progress(db, transfer, source_path, dest_path, job.delete_source_after_transfer)
            )
            self.current_transfers[transfer.id] = transfer_task
            
            # Wait for completion
            await transfer_task
            
            # Update transfer status
            transfer.status = TransferStatus.COMPLETED
            transfer.completed_at = datetime.now(timezone.utc)
            transfer.progress_percentage = 100.0
            await db.commit()
            
            # Update endpoint statistics
            await self._update_endpoint_stats(db, job.source_endpoint_id, job.destination_endpoint_id, transfer.file_size)
            
        except asyncio.CancelledError:
            transfer.status = TransferStatus.CANCELLED
            await db.commit()
            raise
        except Exception as e:
            transfer.status = TransferStatus.FAILED
            transfer.error_message = str(e)
            await db.commit()
            raise
        finally:
            self.current_transfers.pop(transfer.id, None)
    
    def _build_remote_path(self, remote_name: str, endpoint: Endpoint, base_path: str, file_path: str) -> str:
        """Build the full remote path for rclone"""
        # For source paths, use base_path as the directory to scan
        # For destination paths, combine base_path with file_name
        
        # If this is being called for a full file path (source), just use base_path
        # If this is being called for destination, we need to combine paths
        if file_path.startswith('/'):
            # file_path is absolute (source scenario)
            path = file_path
        else:
            # file_path is relative (destination scenario)
            if base_path == '/' or not base_path:
                path = file_path
            elif file_path:
                # Properly join paths
                path = str(Path(base_path) / file_path)
            else:
                # If no file_path provided, just use base_path
                path = base_path
        
        # Let the rclone service build the final path
        return self.rclone_service._build_path(remote_name, path)
    
    def _apply_path_template(self, template: str, source_file: str) -> str:
        """Apply variables to destination path template"""
        import os
        from datetime import datetime
        
        filename = os.path.basename(source_file)
        name_without_ext, ext = os.path.splitext(filename)
        now = datetime.now()
        
        replacements = {
            '{filename}': filename,
            '{original_filename}': filename,  # Alias for {filename}
            '{name}': name_without_ext,
            '{ext}': ext,
            '{year}': str(now.year),
            '{month}': f"{now.month:02d}",
            '{day}': f"{now.day:02d}",
            '{hour}': f"{now.hour:02d}",
            '{minute}': f"{now.minute:02d}",
            '{timestamp}': str(int(now.timestamp())),
        }
        
        result = template
        for key, value in replacements.items():
            result = result.replace(key, value)
        
        # PHASE 1: Log template substitution for tracking
        if template != result:
            logger.info(f"[FILE_TRACKING] Template substitution: '{template}' -> '{result}' (source file: {source_file})")
            
        return result
    
    async def _run_transfer_with_progress(self, db, transfer: Transfer, source: str, dest: str, delete_source: bool):
        """Run the transfer and monitor progress"""
        logger.info(f"Starting transfer: {source} -> {dest}")
        
        # Start the transfer
        process = await self.rclone_service.start_transfer(
            source=source,
            dest=dest,
            delete_source=delete_source
        )
        
        # Collect stderr for error reporting
        stderr_lines = []
        
        # Monitor progress
        while True:
            try:
                # Check if process is still running
                if process.returncode is not None:
                    break
                
                # Read any stderr output
                try:
                    stderr_line = await asyncio.wait_for(process.stderr.readline(), timeout=0.1)
                    if stderr_line:
                        line = stderr_line.decode().strip()
                        stderr_lines.append(line)
                        logger.debug(f"Rclone stderr: {line}")
                except asyncio.TimeoutError:
                    pass
                
                # Get progress from rclone (this would parse rclone's JSON output)
                progress_info = await self.rclone_service.get_transfer_progress(process)
                
                if progress_info:
                    transfer.bytes_transferred = progress_info.get('bytes', 0)
                    transfer.progress_percentage = progress_info.get('percentage', 0)
                    transfer.transfer_rate = progress_info.get('rate', 0)
                    transfer.eta = progress_info.get('eta')
                    await db.commit()
                
                await asyncio.sleep(1)  # Update every second
                
            except Exception as e:
                logger.error(f"Error monitoring transfer {transfer.id}: {e}")
                break
        
        # Read any remaining stderr
        remaining_stderr = await process.stderr.read()
        if remaining_stderr:
            stderr_lines.extend(remaining_stderr.decode().strip().split('\n'))
        
        # Check final status
        if process.returncode != 0:
            error_msg = '\n'.join(stderr_lines[-10:])  # Last 10 lines of error
            logger.error(f"Rclone failed with code {process.returncode}: {error_msg}")
            raise Exception(f"Rclone failed: {error_msg}")
    
    async def _update_endpoint_stats(self, db, source_id: str, dest_id: str, bytes_transferred: int):
        """Update endpoint statistics after successful transfer"""
        # Update source endpoint
        await db.execute(
            update(Endpoint)
            .where(Endpoint.id == source_id)
            .values(
                total_transfers=Endpoint.total_transfers + 1,
                total_bytes_transferred=Endpoint.total_bytes_transferred + bytes_transferred
            )
        )
        
        # Update destination endpoint
        await db.execute(
            update(Endpoint)
            .where(Endpoint.id == dest_id)
            .values(
                total_transfers=Endpoint.total_transfers + 1,
                total_bytes_transferred=Endpoint.total_bytes_transferred + bytes_transferred
            )
        )
        
        await db.commit()
    
    async def _process_chain_jobs(self, db, parent_job: Job, successful_transfers: list = None):
        """Process any chain jobs after parent job completion"""
        try:
            # PHASE 3: Check if we need to create per-file chain jobs
            if successful_transfers and parent_job.config and 'chain_rules' in parent_job.config:
                logger.info(f"[CHAIN_FIX] Creating per-file chain jobs for {len(successful_transfers)} transfers")
                # Get the actual Transfer objects from the database
                from app.models.transfer import Transfer
                transfer_ids = [t['transfer_id'] for t in successful_transfers if 'transfer_id' in t]
                
                if transfer_ids:
                    result = await db.execute(
                        select(Transfer).where(Transfer.id.in_(transfer_ids))
                    )
                    transfers = result.scalars().all()
                    
                    if transfers:
                        # Import ChainJobService to create per-file chain jobs
                        from app.services.chain_job_service import ChainJobService
                        chain_rules = parent_job.config['chain_rules']
                        
                        # Create chain jobs for each successful transfer
                        new_chain_jobs = await ChainJobService.create_chain_jobs(
                            parent_job, chain_rules, db, per_file_transfers=transfers
                        )
                        logger.info(f"[CHAIN_FIX] Created {len(new_chain_jobs)} per-file chain jobs")
            
            # Check if there are chain jobs waiting for this parent (legacy or newly created)
            result = await db.execute(
                select(Job).where(
                    Job.type == JobType.CHAINED,
                    Job.parent_job_id == parent_job.id,
                    Job.status == JobStatus.PENDING
                )
            )
            chain_jobs = result.scalars().all()
            
            for chain_job in chain_jobs:
                # Queue the chain job for processing
                chain_job.status = JobStatus.QUEUED
                await db.commit()
                
                await redis_manager.enqueue_job(chain_job.id)
                logger.info(f"Queued chain job {chain_job.id} after parent {parent_job.id} completed")
                
            # Also check if parent job had transfer template with chain rules
            if parent_job.config and 'transfer_template_id' in parent_job.config:
                # Update transfer template success count
                from app.models.transfer_template import TransferTemplate
                result = await db.execute(
                    select(TransferTemplate).where(TransferTemplate.id == parent_job.config['transfer_template_id'])
                )
                transfer_template = result.scalar_one_or_none()
                
                if transfer_template:
                    transfer_template.successful_transfers += 1
                    await db.commit()
                    
        except Exception as e:
            logger.error(f"Error processing chain jobs for {parent_job.id}: {e}")


async def main():
    """Main entry point for the worker"""
    processor = JobProcessor()
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        asyncio.create_task(processor.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await processor.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        await processor.stop()


if __name__ == "__main__":
    asyncio.run(main())