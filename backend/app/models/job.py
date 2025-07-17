from sqlalchemy import Column, String, DateTime, Integer, Text, Enum as SQLEnum, JSON, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobType(str, enum.Enum):
    MANUAL = "manual"
    EVENT_TRIGGERED = "event_triggered"
    SCHEDULED = "scheduled"
    CHAINED = "chained"


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String(200), nullable=False)  # Add name field
    type = Column(SQLEnum(JobType), nullable=False, default=JobType.MANUAL)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING)
    
    # Source and destination
    source_endpoint_id = Column(String, ForeignKey("endpoints.id"), nullable=False)
    source_path = Column(String, nullable=False)
    destination_endpoint_id = Column(String, ForeignKey("endpoints.id"), nullable=False)
    destination_path = Column(String, nullable=False)
    
    # File patterns and filters
    file_pattern = Column(String, default="*")
    delete_source_after_transfer = Column(Boolean, default=False)
    
    # Progress tracking
    total_files = Column(Integer, default=0)
    transferred_files = Column(Integer, default=0)
    total_bytes = Column(Integer, default=0)
    transferred_bytes = Column(Integer, default=0)
    progress_percentage = Column(Integer, default=0)
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Chaining
    parent_job_id = Column(String, nullable=True)
    chain_config = Column(JSON, nullable=True)  # For secondary destinations
    
    # Event metadata
    transfer_template_id = Column(String, nullable=True)
    event_metadata = Column(JSON, nullable=True)  # S3 event data, file path, etc.
    
    # Schedule and activity
    schedule = Column(String, nullable=True)  # cron expression or preset
    is_active = Column(Boolean, default=True)
    config = Column(JSON, nullable=True, default=dict)
    
    # Run statistics
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    
    # User who created the job (for manual jobs)
    created_by = Column(String, nullable=True)
    
    # Relationships
    transfers = relationship("Transfer", back_populates="job", cascade="all, delete-orphan")
    source_endpoint = relationship("Endpoint", foreign_keys=[source_endpoint_id])
    destination_endpoint = relationship("Endpoint", foreign_keys=[destination_endpoint_id])