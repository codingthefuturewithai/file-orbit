"""Tests documenting KNOWN ISSUES with chain rules functionality

These tests are expected to FAIL and document the behavior described in CP-9.
Chain rules currently DO NOT work correctly for:
- Batch transfers with wildcards (e.g., *.mp4)
- Manual template execution with file patterns

Root cause: Chain jobs are created with unresolved template variables like {original_filename}
instead of actual file paths.

See /docs/CHAIN_RULES_FIX.md for proposed fix.
"""
import pytest
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from app.models.transfer_template import TransferTemplate, EventType
from app.models.job import Job, JobStatus, JobType
from app.services.chain_job_service import ChainJobService


@pytest.mark.xfail(reason="CP-9: Chain rules fail for batch transfers")
class TestBatchTransferChainRules:
    """Test chain rules with batch transfers (CURRENTLY BROKEN)"""
    
    async def test_batch_transfer_chain_jobs_have_unresolved_paths(
        self, db: AsyncSession, test_endpoints
    ):
        """Test that batch transfers create chain jobs with unresolved template variables"""
        # Create a parent job representing a batch transfer
        parent_job = Job(
            id=str(uuid.uuid4()),
            name="Batch Transfer",
            type=JobType.MANUAL,
            source_endpoint_id="source-endpoint",
            source_path="/videos/",  # Directory path
            destination_endpoint_id="primary-endpoint",
            destination_path="/primary/2025/01/",  # Directory path
            file_pattern="*.mp4",  # Wildcard pattern
            status=JobStatus.COMPLETED,
            created_at=datetime.utcnow()
        )
        
        db.add(parent_job)
        await db.commit()
        
        # Chain rules with template variables
        chain_rules = [
            {
                "endpoint_id": "backup-endpoint",
                "path_template": "/backup/{year}/{month}/{original_filename}"
            }
        ]
        
        # Create chain jobs
        chain_jobs = await ChainJobService.create_chain_jobs(
            parent_job, chain_rules, db
        )
        
        # This is the CURRENT broken behavior
        assert len(chain_jobs) == 1
        chain_job = chain_jobs[0]
        
        # BUG: The destination path still contains unresolved template variable
        assert "{original_filename}" in chain_job.destination_path
        
        # BUG: The source path is a directory, not individual files
        assert chain_job.source_path == "/primary/2025/01/"
        
        # This chain job will fail when worker tries to process it
        # because rclone can't transfer a directory to a path with {original_filename}
    
    async def test_manual_template_execution_with_wildcards_broken(
        self, client: AsyncClient, db: AsyncSession, test_endpoints
    ):
        """Test that manual template execution with wildcards creates broken chain jobs"""
        # Create template with wildcards
        template = TransferTemplate(
            id="wildcard-template",
            name="Wildcard Template",
            event_type=EventType.MANUAL_TRIGGER,
            is_active=True,
            source_config={"path": "/videos"},
            source_endpoint_id="source-endpoint",
            destination_endpoint_id="primary-endpoint",
            destination_path_template="/primary/{year}/{month}/{original_filename}",
            file_pattern="*.mp4",
            chain_rules=[
                {
                    "endpoint_id": "backup-endpoint",
                    "path_template": "/backup/{year}/{original_filename}"
                }
            ]
        )
        
        db.add(template)
        await db.commit()
        
        # Execute the template
        response = await client.post(
            f"/api/v1/transfer-templates/{template.id}/execute"
        )
        
        assert response.status_code == 201
        parent_job_id = response.json()["id"]
        
        # Get chain jobs
        from sqlalchemy import select
        result = await db.execute(
            select(Job).where(Job.parent_job_id == parent_job_id)
        )
        chain_jobs = result.scalars().all()
        
        # Chain jobs are created but with unresolved paths
        assert len(chain_jobs) == 1
        chain_job = chain_jobs[0]
        
        # BUG: Both paths contain unresolved template variables
        assert "{original_filename}" in chain_job.source_path
        assert "{original_filename}" in chain_job.destination_path


@pytest.mark.xfail(reason="CP-9: Need file-level chain job creation")
class TestProposedChainRuleFixes:
    """Test the proposed fix for chain rules with batch transfers"""
    
    async def test_chain_jobs_should_be_created_per_file(
        self, db: AsyncSession, test_endpoints
    ):
        """Test that chain jobs should be created for each transferred file"""
        # This test documents the DESIRED behavior
        
        # Parent job for batch transfer
        parent_job = Job(
            id=str(uuid.uuid4()),
            name="Batch Transfer",
            type=JobType.MANUAL,
            source_endpoint_id="source-endpoint",
            source_path="/videos/",
            destination_endpoint_id="primary-endpoint",
            destination_path="/primary/2025/01/",
            file_pattern="*.mp4",
            status=JobStatus.COMPLETED,
            created_at=datetime.utcnow(),
            # This is what we need - track individual files
            config={
                "transferred_files": [
                    {
                        "source": "/videos/movie1.mp4",
                        "destination": "/primary/2025/01/movie1.mp4"
                    },
                    {
                        "source": "/videos/movie2.mp4",
                        "destination": "/primary/2025/01/movie2.mp4"
                    }
                ]
            }
        )
        
        db.add(parent_job)
        await db.commit()
        
        # Chain rules
        chain_rules = [
            {
                "endpoint_id": "backup-endpoint",
                "path_template": "/backup/{year}/{month}/{filename}"
            }
        ]
        
        # PROPOSED: ChainJobService should create jobs per file
        # This would require modifying create_chain_jobs to:
        # 1. Check if parent job has transferred_files in config
        # 2. Create one chain job per transferred file
        # 3. Each chain job has specific source/destination paths
        
        # Expected result (not current behavior):
        # - 2 chain jobs created (one per file)
        # - Each has resolved paths like:
        #   - source: /primary/2025/01/movie1.mp4
        #   - destination: /backup/2025/01/movie1.mp4


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-x"])