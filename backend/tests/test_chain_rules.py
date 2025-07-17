"""Tests for chain rules functionality

These tests document the CURRENT behavior of chain rules as of July 16, 2025.
Chain rules currently work for:
- Single file transfers
- Event-triggered transfers with specific files

Known issues (not tested here, see CP-9):
- Chain rules FAIL for batch transfers with wildcards
- Chain rules FAIL for manual template execution with file patterns
"""
import pytest
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from app.models.transfer_template import TransferTemplate, EventType
from app.models.job import Job, JobStatus, JobType
from app.models.endpoint import Endpoint, EndpointType
from app.services.chain_job_service import ChainJobService
from app.services.redis_manager import redis_manager


@pytest.fixture
async def test_endpoints(db: AsyncSession):
    """Create test endpoints for chain rules"""
    endpoints = []
    
    # Source endpoint
    source = Endpoint(
        id="source-endpoint",
        name="Source S3",
        type=EndpointType.S3,
        config={"bucket": "source-bucket"},
        is_active=True
    )
    endpoints.append(source)
    
    # Primary destination
    primary = Endpoint(
        id="primary-endpoint",
        name="Primary Storage",
        type=EndpointType.S3,
        config={"bucket": "primary-bucket"},
        is_active=True
    )
    endpoints.append(primary)
    
    # Backup destination
    backup = Endpoint(
        id="backup-endpoint",
        name="Backup Storage",
        type=EndpointType.S3,
        config={"bucket": "backup-bucket"},
        is_active=True
    )
    endpoints.append(backup)
    
    # Archive destination
    archive = Endpoint(
        id="archive-endpoint",
        name="Archive Storage",
        type=EndpointType.S3,
        config={"bucket": "archive-bucket"},
        is_active=True
    )
    endpoints.append(archive)
    
    for endpoint in endpoints:
        db.add(endpoint)
    await db.commit()
    
    return endpoints


@pytest.fixture
async def test_template_with_chains(db: AsyncSession, test_endpoints):
    """Create a test template with chain rules"""
    template = TransferTemplate(
        id="test-template",
        name="Test Template with Chains",
        description="Template for testing chain rules",
        event_type=EventType.MANUAL_TRIGGER,
        is_active=True,
        source_config={"path": "/test/source"},
        source_endpoint_id="source-endpoint",
        destination_endpoint_id="primary-endpoint",
        destination_path_template="/primary/{year}/{month}/{filename}",
        chain_rules=[
            {
                "endpoint_id": "backup-endpoint",
                "path_template": "/backup/{year}/{month}/{filename}"
            },
            {
                "endpoint_id": "archive-endpoint",
                "path_template": "/archive/{year}/{filename}"
            }
        ],
        file_pattern="*.mp4"
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return template


@pytest.mark.asyncio
class TestChainJobService:
    """Test ChainJobService functionality"""
    
    async def test_create_chain_jobs(self, db: AsyncSession, test_endpoints):
        """Test creating chain jobs from a parent job"""
        # Create parent job
        parent_job = Job(
            id=str(uuid.uuid4()),
            name="Test Parent Job",
            type=JobType.MANUAL,
            source_endpoint_id="source-endpoint",
            source_path="/test/file.mp4",
            destination_endpoint_id="primary-endpoint",
            destination_path="/primary/2025/01/file.mp4",
            file_pattern="*.mp4",
            status=JobStatus.COMPLETED,
            created_at=datetime.utcnow()
        )
        
        db.add(parent_job)
        await db.commit()
        
        # Define chain rules
        chain_rules = [
            {
                "endpoint_id": "backup-endpoint",
                "path_template": "/backup/{year}/{month}/{filename}"
            },
            {
                "endpoint_id": "archive-endpoint",
                "path_template": "/archive/{year}/{filename}"
            }
        ]
        
        # Create chain jobs
        chain_jobs = await ChainJobService.create_chain_jobs(
            parent_job, chain_rules, db
        )
        
        assert len(chain_jobs) == 2
        
        # Verify first chain job
        chain1 = chain_jobs[0]
        assert chain1.type == JobType.CHAINED
        assert chain1.parent_job_id == parent_job.id
        assert chain1.source_endpoint_id == parent_job.destination_endpoint_id
        assert chain1.source_path == parent_job.destination_path
        assert chain1.destination_endpoint_id == "backup-endpoint"
        assert "/backup/" in chain1.destination_path
        assert "file.mp4" in chain1.destination_path
        assert chain1.status == JobStatus.PENDING
        
        # Verify second chain job
        chain2 = chain_jobs[1]
        assert chain2.type == JobType.CHAINED
        assert chain2.parent_job_id == parent_job.id
        assert chain2.destination_endpoint_id == "archive-endpoint"
        assert "/archive/" in chain2.destination_path
        assert "file.mp4" in chain2.destination_path
    
    async def test_path_template_substitution(self):
        """Test path template variable substitution"""
        template = "/data/{year}/{month}/{day}/{filename}"
        source_path = "/source/test_video.mp4"
        
        result = ChainJobService._apply_path_template(template, source_path)
        
        now = datetime.now()
        assert f"/{now.year}/" in result
        assert f"/{now.month:02d}/" in result
        assert f"/{now.day:02d}/" in result
        assert "test_video.mp4" in result
    
    async def test_get_chain_jobs(self, db: AsyncSession, test_endpoints):
        """Test retrieving chain jobs for a parent"""
        # Create parent job
        parent_job = Job(
            id=str(uuid.uuid4()),
            name="Parent Job",
            type=JobType.MANUAL,
            source_endpoint_id="source-endpoint",
            source_path="/test/file.mp4",
            destination_endpoint_id="primary-endpoint",
            destination_path="/primary/file.mp4",
            status=JobStatus.COMPLETED,
            created_at=datetime.utcnow()
        )
        
        db.add(parent_job)
        
        # Create chain jobs
        for i in range(2):
            chain_job = Job(
                id=str(uuid.uuid4()),
                name=f"Chain Job {i+1}",
                type=JobType.CHAINED,
                parent_job_id=parent_job.id,
                source_endpoint_id="primary-endpoint",
                source_path="/primary/file.mp4",
                destination_endpoint_id="backup-endpoint",
                destination_path=f"/backup{i}/file.mp4",
                status=JobStatus.PENDING,
                created_at=datetime.utcnow()
            )
            db.add(chain_job)
        
        await db.commit()
        
        # Retrieve chain jobs
        chain_jobs = await ChainJobService.get_chain_jobs(parent_job.id, db)
        
        assert len(chain_jobs) == 2
        assert all(job.parent_job_id == parent_job.id for job in chain_jobs)
        assert all(job.type == JobType.CHAINED for job in chain_jobs)


class TestChainRulesAPI:
    """Test chain rules through API endpoints"""
    
    async def test_execute_template_with_chains(
        self, client: AsyncClient, db: AsyncSession, 
        test_template_with_chains, test_endpoints
    ):
        """Test executing a template creates chain jobs"""
        response = await client.post(
            f"/api/v1/transfer-templates/{test_template_with_chains.id}/execute"
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify primary job was created
        assert data["name"] == "Test Template with Chains - Manual"
        assert data["type"] == "manual"
        assert data["status"] == "queued"
        
        # Verify chain job info in response
        assert "config" in data
        assert data["config"]["chain_job_count"] == 2
        assert len(data["config"]["chain_job_ids"]) == 2
        
        # Verify chain jobs in database
        from sqlalchemy import select
        result = await db.execute(
            select(Job).where(Job.parent_job_id == data["id"])
        )
        chain_jobs = result.scalars().all()
        
        assert len(chain_jobs) == 2
        assert all(job.type == JobType.CHAINED for job in chain_jobs)
        assert all(job.status == JobStatus.PENDING for job in chain_jobs)
    
    async def test_create_template_validates_chain_endpoints(
        self, client: AsyncClient, db: AsyncSession, test_endpoints
    ):
        """Test that chain rule endpoints are validated"""
        template_data = {
            "name": "Template with Invalid Chain",
            "event_type": "manual",
            "is_active": True,
            "source_config": {"path": "/source"},
            "source_endpoint_id": "source-endpoint",
            "destination_endpoint_id": "primary-endpoint",
            "destination_path_template": "/dest/{filename}",
            "chain_rules": [
                {
                    "endpoint_id": "non-existent-endpoint",
                    "path_template": "/backup/{filename}"
                }
            ]
        }
        
        response = await client.post(
            "/api/v1/transfer-templates",
            json=template_data
        )
        
        assert response.status_code == 400
        assert "Chain endpoint non-existent-endpoint not found" in response.json()["detail"]
    
    async def test_execute_inactive_template_fails(
        self, client: AsyncClient, db: AsyncSession, test_template_with_chains
    ):
        """Test that executing an inactive template fails"""
        # Deactivate template
        test_template_with_chains.is_active = False
        await db.commit()
        
        response = await client.post(
            f"/api/v1/transfer-templates/{test_template_with_chains.id}/execute"
        )
        
        assert response.status_code == 400
        assert "is not active" in response.json()["detail"]


class TestWorkerChainProcessing:
    """Test worker processing of chain jobs"""
    
    async def test_worker_queues_chain_jobs_after_parent_success(
        self, db: AsyncSession, test_endpoints, redis_mock
    ):
        """Test that worker queues chain jobs when parent completes"""
        # This would require mocking the worker and redis
        # For now, we'll test the query logic
        from sqlalchemy import select
        
        # Create parent job
        parent_job = Job(
            id="parent-123",
            name="Parent Job",
            type=JobType.MANUAL,
            source_endpoint_id="source-endpoint",
            destination_endpoint_id="primary-endpoint",
            source_path="/test.mp4",
            destination_path="/primary/test.mp4",
            status=JobStatus.COMPLETED,
            created_at=datetime.utcnow()
        )
        
        # Create chain job
        chain_job = Job(
            id="chain-123",
            name="Chain Job",
            type=JobType.CHAINED,
            parent_job_id=parent_job.id,
            source_endpoint_id="primary-endpoint",
            destination_endpoint_id="backup-endpoint",
            source_path="/primary/test.mp4",
            destination_path="/backup/test.mp4",
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        db.add(parent_job)
        db.add(chain_job)
        await db.commit()
        
        # Query that worker uses
        result = await db.execute(
            select(Job).where(
                Job.type == JobType.CHAINED,
                Job.parent_job_id == parent_job.id,
                Job.status == JobStatus.PENDING
            )
        )
        chain_jobs = result.scalars().all()
        
        assert len(chain_jobs) == 1
        assert chain_jobs[0].id == "chain-123"


class TestSingleFileChainRules:
    """Test chain rules with single file transfers (CURRENTLY WORKING)"""
    
    async def test_single_file_transfer_with_chains(
        self, client: AsyncClient, db: AsyncSession,
        test_template_with_chains, test_endpoints
    ):
        """Test that chain rules work correctly for single file transfers"""
        # Create a job that simulates a single file transfer
        parent_job = Job(
            id=str(uuid.uuid4()),
            name="Single File Transfer",
            type=JobType.MANUAL,
            source_endpoint_id="source-endpoint",
            source_path="/videos/movie.mp4",  # Specific file path
            destination_endpoint_id="primary-endpoint",
            destination_path="/primary/2025/01/movie.mp4",  # Resolved path
            file_pattern=None,  # No pattern for single file
            status=JobStatus.COMPLETED,
            created_at=datetime.utcnow(),
            config={"transfer_template_id": test_template_with_chains.id}
        )
        
        db.add(parent_job)
        await db.commit()
        
        # Create chain jobs using the service
        chain_rules = test_template_with_chains.chain_rules
        chain_jobs = await ChainJobService.create_chain_jobs(
            parent_job, chain_rules, db
        )
        
        # Verify chain jobs have properly resolved paths
        assert len(chain_jobs) == 2
        
        # First chain job to backup
        assert chain_jobs[0].source_path == "/primary/2025/01/movie.mp4"
        assert chain_jobs[0].destination_path == "/backup/2025/01/movie.mp4"
        assert chain_jobs[0].source_endpoint_id == "primary-endpoint"
        assert chain_jobs[0].destination_endpoint_id == "backup-endpoint"
        
        # Second chain job to archive
        assert chain_jobs[1].source_path == "/primary/2025/01/movie.mp4"
        assert chain_jobs[1].destination_path == "/archive/2025/movie.mp4"
        assert chain_jobs[1].source_endpoint_id == "primary-endpoint"
        assert chain_jobs[1].destination_endpoint_id == "archive-endpoint"
    
    async def test_event_triggered_single_file_chain(
        self, db: AsyncSession, test_endpoints
    ):
        """Test chain rules for event-triggered single file transfers"""
        # Create an event-triggered template
        template = TransferTemplate(
            id="event-template",
            name="Event Triggered Template",
            event_type=EventType.FILE_CREATED,
            is_active=True,
            source_config={"path": "/incoming"},
            source_endpoint_id="source-endpoint",
            destination_endpoint_id="primary-endpoint",
            destination_path_template="/processed/{year}/{month}/{filename}",
            chain_rules=[
                {
                    "endpoint_id": "backup-endpoint",
                    "path_template": "/backup/{year}/{filename}"
                }
            ]
        )
        
        db.add(template)
        await db.commit()
        
        # Simulate an event-triggered job for a specific file
        event_job = Job(
            id=str(uuid.uuid4()),
            name="Event: new_video.mp4",
            type=JobType.EVENT_TRIGGERED,
            source_endpoint_id="source-endpoint",
            source_path="/incoming/new_video.mp4",  # Specific file from event
            destination_endpoint_id="primary-endpoint",
            destination_path="/processed/2025/01/new_video.mp4",  # Resolved path
            status=JobStatus.COMPLETED,
            created_at=datetime.utcnow(),
            config={"transfer_template_id": template.id}
        )
        
        db.add(event_job)
        await db.commit()
        
        # Create chain job
        chain_jobs = await ChainJobService.create_chain_jobs(
            event_job, template.chain_rules, db
        )
        
        assert len(chain_jobs) == 1
        assert chain_jobs[0].source_path == "/processed/2025/01/new_video.mp4"
        assert chain_jobs[0].destination_path == "/backup/2025/new_video.mp4"


class TestChainJobStatusTransitions:
    """Test chain job status transitions and worker integration"""
    
    async def test_chain_jobs_remain_pending_until_parent_completes(
        self, db: AsyncSession, test_endpoints
    ):
        """Test that chain jobs stay PENDING until parent completes"""
        # Create parent job in RUNNING state
        parent_job = Job(
            id="parent-running",
            name="Running Parent",
            type=JobType.MANUAL,
            source_endpoint_id="source-endpoint",
            destination_endpoint_id="primary-endpoint",
            source_path="/test.mp4",
            destination_path="/primary/test.mp4",
            status=JobStatus.RUNNING,  # Still running
            created_at=datetime.utcnow()
        )
        
        db.add(parent_job)
        await db.commit()
        
        # Create chain job
        chain_rules = [{"endpoint_id": "backup-endpoint", "path_template": "/backup/{filename}"}]
        chain_jobs = await ChainJobService.create_chain_jobs(parent_job, chain_rules, db)
        
        assert len(chain_jobs) == 1
        assert chain_jobs[0].status == JobStatus.PENDING
        assert chain_jobs[0].parent_job_id == parent_job.id
    
    async def test_worker_queues_chain_jobs_on_parent_success(
        self, db: AsyncSession, test_endpoints
    ):
        """Test that worker queues chain jobs when parent succeeds"""
        from backend.worker import Worker
        
        # Create completed parent job
        parent_job = Job(
            id="parent-complete",
            name="Completed Parent",
            type=JobType.MANUAL,
            source_endpoint_id="source-endpoint",
            destination_endpoint_id="primary-endpoint",
            source_path="/test.mp4",
            destination_path="/primary/test.mp4",
            status=JobStatus.COMPLETED,
            created_at=datetime.utcnow()
        )
        
        # Create pending chain job
        chain_job = Job(
            id="chain-pending",
            name="Chain Job",
            type=JobType.CHAINED,
            parent_job_id=parent_job.id,
            source_endpoint_id="primary-endpoint",
            destination_endpoint_id="backup-endpoint",
            source_path="/primary/test.mp4",
            destination_path="/backup/test.mp4",
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        db.add(parent_job)
        db.add(chain_job)
        await db.commit()
        
        # Simulate worker processing chain jobs
        with patch.object(redis_manager, 'enqueue_job', new_callable=AsyncMock) as mock_enqueue:
            worker = Worker()
            await worker._process_chain_jobs(db, parent_job)
            
            # Verify chain job was queued
            await db.refresh(chain_job)
            assert chain_job.status == JobStatus.QUEUED
            mock_enqueue.assert_called_once_with("chain-pending")


class TestChainRulePathTemplates:
    """Test path template substitution in chain rules"""
    
    def test_path_template_with_all_variables(self):
        """Test path template substitution with all supported variables"""
        template = "/data/{year}/{month}/{day}/{basename}_{extension}"
        source_path = "/source/video_file.mp4"
        
        result = ChainJobService._apply_path_template(template, source_path)
        
        now = datetime.now()
        expected = f"/data/{now.year}/{now.month:02d}/{now.day:02d}/video_file_mp4"
        assert result == expected
    
    def test_path_template_preserves_literal_text(self):
        """Test that literal text in templates is preserved"""
        template = "/archive/videos/{year}/backup_{filename}"
        source_path = "/tmp/important.mov"
        
        result = ChainJobService._apply_path_template(template, source_path)
        
        now = datetime.now()
        assert result == f"/archive/videos/{now.year}/backup_important.mov"
    
    def test_path_template_handles_nested_paths(self):
        """Test template substitution with nested source paths"""
        template = "/dest/{filename}"
        source_path = "/very/long/nested/path/to/file.txt"
        
        result = ChainJobService._apply_path_template(template, source_path)
        
        assert result == "/dest/file.txt"


class TestChainRuleValidation:
    """Test validation of chain rules in templates"""
    
    async def test_create_template_with_invalid_chain_endpoint(
        self, client: AsyncClient, db: AsyncSession, test_endpoints
    ):
        """Test that invalid endpoint IDs in chain rules are rejected"""
        template_data = {
            "name": "Invalid Chain Template",
            "event_type": "manual",
            "is_active": True,
            "source_config": {"path": "/source"},
            "source_endpoint_id": "source-endpoint",
            "destination_endpoint_id": "primary-endpoint",
            "destination_path_template": "/dest/{filename}",
            "chain_rules": [
                {
                    "endpoint_id": "non-existent-endpoint",
                    "path_template": "/backup/{filename}"
                }
            ]
        }
        
        response = await client.post("/api/v1/transfer-templates", json=template_data)
        
        assert response.status_code == 400
        assert "Chain endpoint non-existent-endpoint not found" in response.json()["detail"]
    
    async def test_create_template_with_empty_chain_rules(
        self, client: AsyncClient, db: AsyncSession, test_endpoints
    ):
        """Test that templates can be created with empty chain rules"""
        template_data = {
            "name": "No Chain Template",
            "event_type": "manual",
            "is_active": True,
            "source_config": {"path": "/source"},
            "source_endpoint_id": "source-endpoint",
            "destination_endpoint_id": "primary-endpoint",
            "destination_path_template": "/dest/{filename}",
            "chain_rules": []
        }
        
        response = await client.post("/api/v1/transfer-templates", json=template_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["chain_rules"] == []


class TestChainJobRecovery:
    """Test recovery and error handling for chain jobs"""
    
    async def test_chain_job_creation_continues_on_partial_failure(
        self, db: AsyncSession, test_endpoints
    ):
        """Test that chain job creation continues even if one fails"""
        parent_job = Job(
            id=str(uuid.uuid4()),
            name="Parent Job",
            type=JobType.MANUAL,
            source_endpoint_id="source-endpoint",
            destination_endpoint_id="primary-endpoint",
            source_path="/test.mp4",
            destination_path="/primary/test.mp4",
            status=JobStatus.COMPLETED,
            created_at=datetime.utcnow()
        )
        
        db.add(parent_job)
        await db.commit()
        
        # Chain rules with one invalid endpoint
        chain_rules = [
            {"endpoint_id": "backup-endpoint", "path_template": "/backup/{filename}"},
            {"endpoint_id": None, "path_template": "/invalid/{filename}"},  # This will fail
            {"endpoint_id": "archive-endpoint", "path_template": "/archive/{filename}"}
        ]
        
        # Create chain jobs - should create 2 out of 3
        with patch('app.services.chain_job_service.logger') as mock_logger:
            chain_jobs = await ChainJobService.create_chain_jobs(
                parent_job, chain_rules, db
            )
            
            # Should have logged the error
            assert mock_logger.error.called
        
        # Should have created the valid chain jobs
        assert len(chain_jobs) == 2
        assert chain_jobs[0].destination_endpoint_id == "backup-endpoint"
        assert chain_jobs[1].destination_endpoint_id == "archive-endpoint"


class TestChainJobIntegration:
    """Integration tests for complete chain job flow"""
    
    async def test_manual_template_execution_creates_chain_jobs(
        self, client: AsyncClient, db: AsyncSession,
        test_template_with_chains, test_endpoints
    ):
        """Test complete flow: template execution -> parent job -> chain jobs"""
        # Execute the template
        response = await client.post(
            f"/api/v1/transfer-templates/{test_template_with_chains.id}/execute"
        )
        
        assert response.status_code == 201
        parent_job_data = response.json()
        
        # Verify parent job
        assert parent_job_data["type"] == "manual"
        assert parent_job_data["status"] == "queued"
        
        # Verify chain jobs were created
        assert parent_job_data["config"]["chain_job_count"] == 2
        assert len(parent_job_data["config"]["chain_job_ids"]) == 2
        
        # Get chain jobs from database
        from sqlalchemy import select
        result = await db.execute(
            select(Job).where(Job.parent_job_id == parent_job_data["id"])
        )
        chain_jobs = result.scalars().all()
        
        assert len(chain_jobs) == 2
        for job in chain_jobs:
            assert job.type == JobType.CHAINED
            assert job.status == JobStatus.PENDING
            assert job.parent_job_id == parent_job_data["id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])