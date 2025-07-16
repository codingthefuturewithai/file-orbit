from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class TransferStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Transfer(Base):
    __tablename__ = "transfers"
    
    id = Column(String, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    
    # File information
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Source file path
    file_size = Column(Integer, nullable=False)
    
    # Destination tracking (for chain job support)
    destination_path = Column(String, nullable=True)  # Actual destination path after template substitution
    
    # Transfer progress
    status = Column(SQLEnum(TransferStatus), nullable=False, default=TransferStatus.PENDING)
    bytes_transferred = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)
    transfer_rate = Column(Float, nullable=True)  # Bytes per second
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    eta = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Rclone specific
    rclone_job_id = Column(Integer, nullable=True)  # Rclone RC job ID
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="transfers")