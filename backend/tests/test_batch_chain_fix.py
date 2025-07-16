"""Test that batch transfers with chain rules now work correctly"""
import pytest
import os
import tempfile
import shutil
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import Mock, patch, AsyncMock

from app.models.job import Job, JobStatus, JobType
from app.models.transfer import Transfer, TransferStatus
from app.models.endpoint import Endpoint
from sqlalchemy import select
from app.services.chain_job_service import ChainJobService


class TestBatchChainFix:
    """Test the fix for batch transfers with chain rules"""
    
    @pytest.mark.asyncio
    async def test_batch_transfer_creates_per_file_chains(self, db: AsyncSession):
        """Test that batch transfers now create individual chain jobs per file"""
        # Create test endpoints
        source_endpoint = Endpoint(
            id="source-endpoint",
            name="Source",
            type="local",
            config={"path": "/tmp/source"}
        )
        dest_endpoint = Endpoint(
            id="dest-endpoint", 
            name="Destination",
            type="local",
            config={"path": "/tmp/dest"}
        )
        chain_endpoint = Endpoint(
            id="chain-endpoint",
            name="Chain",
            type="local", 
            config={"path": "/tmp/chain"}
        )
        
        db.add_all([source_endpoint, dest_endpoint, chain_endpoint])
        await db.commit()
        
        # Create parent job with chain rules in config
        parent_job = Job(
            id="parent-123",
            name="Batch Transfer",
            type=JobType.MANUAL,
            source_endpoint_id="source-endpoint",
            destination_endpoint_id="dest-endpoint",
            source_path="/tmp/source",
            destination_path="/tmp/dest/{original_filename}",
            file_pattern="*.mp4",
            status=JobStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            config={
                'chain_rules': [
                    {"endpoint_id": "chain-endpoint", "path_template": "/backup/{year}/{filename}"}
                ]
            }
        )
        
        db.add(parent_job)
        await db.commit()
        
        # Create transfers representing successful file transfers
        transfer1 = Transfer(
            id="transfer-1",
            job_id=parent_job.id,
            file_name="video1.mp4",
            file_path="/tmp/source/video1.mp4",
            destination_path="/tmp/dest/video1.mp4",  # Actual resolved path
            file_size=1000000,
            status=TransferStatus.COMPLETED,
            created_at=datetime.now(timezone.utc)
        )
        
        transfer2 = Transfer(
            id="transfer-2",
            job_id=parent_job.id,
            file_name="video2.mp4",
            file_path="/tmp/source/video2.mp4",
            destination_path="/tmp/dest/video2.mp4",  # Actual resolved path
            file_size=2000000,
            status=TransferStatus.COMPLETED,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add_all([transfer1, transfer2])
        await db.commit()
        
        # Simulate worker creating chain jobs after transfers complete
        chain_jobs = await ChainJobService.create_chain_jobs(
            parent_job,
            parent_job.config['chain_rules'],
            db,
            per_file_transfers=[transfer1, transfer2]
        )
        
        # Verify results
        assert len(chain_jobs) == 2  # One chain job per file
        
        # Check first chain job
        chain1 = chain_jobs[0]
        assert chain1.source_path == "/tmp/dest/video1.mp4"  # Resolved path
        assert chain1.destination_path.endswith("/video1.mp4")  # Contains actual filename
        assert "backup" in chain1.destination_path
        assert str(datetime.now().year) in chain1.destination_path
        assert chain1.file_pattern is None or chain1.file_pattern == '*'  # May inherit pattern
        assert chain1.config['source_file'] == "video1.mp4"
        assert chain1.name == "Batch Transfer - video1.mp4 - Chain 1"
        
        # Check second chain job  
        chain2 = chain_jobs[1]
        assert chain2.source_path == "/tmp/dest/video2.mp4"  # Resolved path
        assert chain2.destination_path.endswith("/video2.mp4")
        assert chain2.config['source_file'] == "video2.mp4"
        assert chain2.name == "Batch Transfer - video2.mp4 - Chain 1"
    
    @pytest.mark.asyncio
    async def test_manual_template_execution_with_wildcards(self, db: AsyncSession):
        """Test that manual template execution with wildcards now works"""
        # Create job from manual template execution
        job = Job(
            id="manual-123",
            name="Manual Template Execution",
            type=JobType.MANUAL,
            source_endpoint_id="source-endpoint",
            destination_endpoint_id="dest-endpoint",
            source_path="/source",
            destination_path="/dest/*",  # Wildcard from template
            file_pattern="*.mp4",
            status=JobStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            config={
                'manual_execution': True,
                'chain_rules': [
                    {"endpoint_id": "backup-endpoint", "path_template": "/archive/{basename}_{year}.{extension}"}
                ]
            }
        )
        
        db.add(job)
        await db.commit()
        
        # Create transfers with resolved paths
        transfers = []
        for i in range(3):
            transfer = Transfer(
                id=f"transfer-{i}",
                job_id=job.id,
                file_name=f"file{i}.mp4",
                file_path=f"/source/file{i}.mp4",
                destination_path=f"/dest/file{i}.mp4",  # Resolved path
                file_size=1000000 * (i + 1),
                status=TransferStatus.COMPLETED,
                created_at=datetime.now(timezone.utc)
            )
            transfers.append(transfer)
            db.add(transfer)
        
        await db.commit()
        
        # Create chain jobs
        chain_jobs = await ChainJobService.create_chain_jobs(
            job,
            job.config['chain_rules'],
            db,
            per_file_transfers=transfers
        )
        
        # Verify
        assert len(chain_jobs) == 3
        
        for i, chain_job in enumerate(chain_jobs):
            assert chain_job.source_path == f"/dest/file{i}.mp4"
            assert f"file{i}_{datetime.now().year}.mp4" in chain_job.destination_path
            assert chain_job.parent_job_id == job.id
            assert chain_job.config['parent_transfer_id'] == f"transfer-{i}"
    
    @pytest.mark.asyncio  
    async def test_mixed_success_failure_batch(self, db: AsyncSession):
        """Test that chain jobs are only created for successful transfers"""
        job = Job(
            id="mixed-123",
            name="Mixed Success/Failure",
            type=JobType.MANUAL,
            source_endpoint_id="source-endpoint",
            destination_endpoint_id="dest-endpoint",
            source_path="/source",
            destination_path="/dest/{filename}",
            status=JobStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            config={
                'chain_rules': [
                    {"endpoint_id": "backup-endpoint", "path_template": "/backup/{filename}"}
                ]
            }
        )
        
        db.add(job)
        await db.commit()
        
        # Mix of successful and failed transfers
        success_transfer = Transfer(
            id="success-1",
            job_id=job.id,
            file_name="success.mp4",
            file_path="/source/success.mp4",
            destination_path="/dest/success.mp4",
            file_size=1000000,
            status=TransferStatus.COMPLETED,
            created_at=datetime.now(timezone.utc)
        )
        
        failed_transfer = Transfer(
            id="failed-1",
            job_id=job.id,
            file_name="failed.mp4",
            file_path="/source/failed.mp4",
            destination_path="/dest/failed.mp4",
            file_size=2000000,
            status=TransferStatus.FAILED,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add_all([success_transfer, failed_transfer])
        await db.commit()
        
        # Only pass successful transfers
        chain_jobs = await ChainJobService.create_chain_jobs(
            job,
            job.config['chain_rules'],
            db,
            per_file_transfers=[success_transfer]  # Only successful ones
        )
        
        # Should only create chain job for successful transfer
        assert len(chain_jobs) == 1
        assert chain_jobs[0].source_path == "/dest/success.mp4"
        assert chain_jobs[0].config['source_file'] == "success.mp4"