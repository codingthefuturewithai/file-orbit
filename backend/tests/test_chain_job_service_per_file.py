"""Tests for ChainJobService per-file chain creation functionality"""
import pytest
from unittest.mock import Mock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chain_job_service import ChainJobService


class TestPerFileChainCreation:
    """Test the new per-file chain creation functionality"""
    
    @pytest.mark.asyncio
    async def test_create_chain_jobs_legacy_mode(self):
        """Test that legacy mode still works when no transfers provided"""
        # Setup mock objects
        parent_job = Mock(
            id="parent-123",
            name="Test Job",
            destination_endpoint_id="endpoint-1",
            destination_path="/dest/test.mp4",
            file_pattern="*.mp4"
        )
        
        chain_rules = [
            {"endpoint_id": "endpoint-2", "path_template": "/backup/{filename}"}
        ]
        
        db = AsyncMock(spec=AsyncSession)
        
        # Call service without per_file_transfers
        result = await ChainJobService.create_chain_jobs(
            parent_job, chain_rules, db
        )
        
        # Should create one chain job
        assert len(result) == 1
        assert result[0].source_path == "/dest/test.mp4"
        assert result[0].destination_path == "/backup/test.mp4"
        assert result[0].file_pattern == "*.mp4"  # Inherits pattern
    
    @pytest.mark.asyncio
    async def test_create_chain_jobs_per_file_mode(self):
        """Test per-file chain creation with multiple transfers"""
        # Setup mock objects
        parent_job = Mock(
            id="parent-123",
            name="Batch Job",
            destination_endpoint_id="endpoint-1",
            destination_path="/dest/{filename}",
            file_pattern="*.mp4"
        )
        
        # Mock transfers with actual destination paths
        transfers = [
            Mock(
                id="transfer-1",
                destination_path="/dest/video1.mp4",
                destination="/dest/video1.mp4"
            ),
            Mock(
                id="transfer-2",
                destination_path="/dest/video2.mp4",
                destination="/dest/video2.mp4"
            )
        ]
        
        chain_rules = [
            {"endpoint_id": "endpoint-2", "path_template": "/backup/{year}/{filename}"},
            {"endpoint_id": "endpoint-3", "path_template": "/archive/{basename}.{extension}"}
        ]
        
        db = AsyncMock(spec=AsyncSession)
        
        # Call service with per_file_transfers
        result = await ChainJobService.create_chain_jobs(
            parent_job, chain_rules, db, per_file_transfers=transfers
        )
        
        # Should create 2 rules × 2 files = 4 chain jobs
        assert len(result) == 4
        
        # Check first file, first rule
        job1 = result[0]
        assert job1.source_path == "/dest/video1.mp4"
        assert "/backup/" in job1.destination_path
        assert "video1.mp4" in job1.destination_path
        assert job1.file_pattern is None  # No pattern for specific files
        assert job1.config['source_file'] == "video1.mp4"
        assert job1.config['parent_transfer_id'] == "transfer-1"
        
        # Check second file, first rule
        job2 = result[2]
        assert job2.source_path == "/dest/video2.mp4"
        assert "video2.mp4" in job2.destination_path
        
        # Check name includes filename
        assert "video1.mp4" in result[0].name
        assert "video2.mp4" in result[2].name
    
    @pytest.mark.asyncio
    async def test_per_file_chain_with_path_templates(self):
        """Test that path templates work correctly with per-file chains"""
        parent_job = Mock(
            id="parent-123",
            name="Test Job",
            destination_endpoint_id="endpoint-1"
        )
        
        transfers = [
            Mock(
                id="transfer-1",
                destination_path="/dest/test_file.mp4",
                destination="/dest/test_file.mp4"
            )
        ]
        
        chain_rules = [
            {"endpoint_id": "endpoint-2", "path_template": "/processed/{basename}_backup.{extension}"}
        ]
        
        db = AsyncMock(spec=AsyncSession)
        
        result = await ChainJobService.create_chain_jobs(
            parent_job, chain_rules, db, per_file_transfers=transfers
        )
        
        assert len(result) == 1
        assert result[0].destination_path == "/processed/test_file_backup.mp4"
    
    @pytest.mark.asyncio
    async def test_empty_transfers_returns_empty_list(self):
        """Test that empty transfers list returns empty result"""
        parent_job = Mock(id="parent-123")
        chain_rules = [{"endpoint_id": "endpoint-2", "path_template": "/{filename}"}]
        db = AsyncMock(spec=AsyncSession)
        
        result = await ChainJobService.create_chain_jobs(
            parent_job, chain_rules, db, per_file_transfers=[]
        )
        
        assert result == []
        db.commit.assert_not_called()