from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.job import JobStatus, JobType


class JobBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: JobType
    source_endpoint_id: str
    destination_endpoint_id: str
    source_path: str
    destination_path: str
    file_pattern: Optional[str] = None
    delete_source_after_transfer: bool = False
    schedule: Optional[str] = None
    is_active: bool = True
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    destination_path: Optional[str] = None
    file_pattern: Optional[str] = None
    delete_source_after_transfer: Optional[bool] = None
    schedule: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class JobResponse(JobBase):
    id: str
    status: JobStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    error_message: Optional[str] = None
    retry_count: int = 0
    progress_percentage: int = 0
    total_files: int = 0
    transferred_files: int = 0
    total_bytes: int = 0
    transferred_bytes: int = 0

    class Config:
        from_attributes = True


class JobExecute(BaseModel):
    force: bool = Field(default=False, description="Force execution even if recently run")