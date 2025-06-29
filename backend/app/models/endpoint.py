from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class EndpointType(str, enum.Enum):
    LOCAL = "local"
    SMB = "smb"
    S3 = "s3"
    SFTP = "sftp"
    FTP = "ftp"
    WEBDAV = "webdav"


class Endpoint(Base):
    __tablename__ = "endpoints"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    type = Column(SQLEnum(EndpointType), nullable=False)
    
    # Connection details (encrypted in production)
    config = Column(JSON, nullable=False)
    # Example configs:
    # S3: {"provider": "s3", "access_key_id": "...", "secret_access_key": "...", "bucket": "my-bucket", "region": "us-east-1"}
    # Local: {"path": "/path/to/dir"}
    # SMB: {"host": "server.ctf.org", "share": "videos", "user": "ctfuser", "domain": "CTF"}

    # Rate limiting settings for the endpoint
    max_concurrent_transfers = Column(Integer, default=5)
    max_bandwidth = Column(Integer, nullable=True)  # Bytes per second, null = unlimited
    
    # Status
    is_active = Column(Boolean, default=True)
    last_connected = Column(DateTime(timezone=True), nullable=True)
    connection_status = Column(String, default="unknown")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Statistics
    total_transfers = Column(Integer, default=0)
    failed_transfers = Column(Integer, default=0)
    total_bytes_transferred = Column(Integer, default=0)