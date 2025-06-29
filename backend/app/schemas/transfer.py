from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.transfer import TransferStatus


class TransferBase(BaseModel):
    job_id: str
    file_name: str
    file_path: str
    file_size: int


class TransferResponse(TransferBase):
    id: str
    status: TransferStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    bytes_transferred: int = 0
    progress_percentage: float = 0.0
    transfer_rate: Optional[float] = None
    eta: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    rclone_job_id: Optional[int] = None

    class Config:
        from_attributes = True


class TransferStats(BaseModel):
    total_transfers: int
    active_transfers: int
    completed_transfers: int
    failed_transfers: int
    total_bytes_transferred: int
    average_transfer_rate: Optional[float] = None