from sqlalchemy import Column, String, Boolean, JSON, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class EventType(str, enum.Enum):
    S3_OBJECT_CREATED = "s3:ObjectCreated"
    FILE_CREATED = "file:created"
    FILE_MODIFIED = "file:modified"
    MANUAL_TRIGGER = "manual"


class TransferTemplate(Base):
    __tablename__ = "transfer_templates"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    
    # Event configuration
    event_type = Column(SQLEnum(EventType), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Source configuration
    source_config = Column(JSON, nullable=False)
    # Examples:
    # S3: {"bucket": "pbs-videos", "prefix": "incoming/", "suffix": ".mp4"}
    # File: {"path": "/mnt/watch", "pattern": "*.mov", "recursive": true}
    
    # Transfer configuration
    source_endpoint_id = Column(String, nullable=False)
    destination_endpoint_id = Column(String, nullable=False)
    destination_path_template = Column(String, nullable=False)
    # Template can include: {year}, {month}, {day}, {filename}, {basename}, {extension}
    
    # Chain configuration (for secondary transfers)
    chain_rules = Column(JSON, nullable=True)
    # Example: [
    #   {"endpoint_id": "secondary1", "path_template": "/archive/{year}/{month}/{filename}"},
    #   {"endpoint_id": "secondary2", "path_template": "/backup/{filename}"}
    # ]
    
    # File handling
    file_pattern = Column(String, default="*")
    delete_source_after_transfer = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    
    # Statistics
    total_triggers = Column(Integer, default=0)
    successful_transfers = Column(Integer, default=0)
    failed_transfers = Column(Integer, default=0)