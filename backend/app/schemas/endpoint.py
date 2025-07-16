from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.endpoint import EndpointType


class EndpointBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: EndpointType
    config: Dict[str, Any]
    max_concurrent_transfers: int = Field(default=5, ge=1, le=100)
    max_bandwidth: Optional[int] = None
    is_active: bool = True


class EndpointCreate(EndpointBase):
    pass


class EndpointUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[EndpointType] = None
    config: Optional[Dict[str, Any]] = None
    max_concurrent_transfers: Optional[int] = Field(None, ge=1, le=100)
    max_bandwidth: Optional[int] = None
    is_active: Optional[bool] = None


class EndpointResponse(EndpointBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_connected: Optional[datetime] = None
    connection_status: str
    total_transfers: int = 0
    failed_transfers: int = 0
    total_bytes_transferred: int = 0

    class Config:
        from_attributes = True