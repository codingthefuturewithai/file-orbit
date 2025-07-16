"""Tests for chain rules functionality"""
import pytest
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from app.models.transfer_template import TransferTemplate, EventType
from app.models.job import Job, JobStatus, JobType
from app.models.endpoint import Endpoint, EndpointType
from app.services.chain_job_service import ChainJobService
from app.core.database import get_db


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
                destination_endpoint_id=f"backup-endpoint",
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])