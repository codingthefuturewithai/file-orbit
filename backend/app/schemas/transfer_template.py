from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.transfer_template import EventType


class ChainRule(BaseModel):
    endpoint_id: str
    path_template: str


class TransferTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    event_type: EventType
    is_active: bool = True
    source_config: Dict[str, Any]
    source_endpoint_id: str
    destination_endpoint_id: str
    destination_path_template: str
    chain_rules: Optional[List[ChainRule]] = Field(default_factory=list)
    file_pattern: Optional[str] = None
    delete_source_after_transfer: bool = False


class TransferTemplateCreate(TransferTemplateBase):
    pass


class TransferTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    source_config: Optional[Dict[str, Any]] = None
    destination_path_template: Optional[str] = None
    chain_rules: Optional[List[ChainRule]] = None
    file_pattern: Optional[str] = None
    delete_source_after_transfer: Optional[bool] = None


class TransferTemplateResponse(TransferTemplateBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_triggered: Optional[datetime] = None
    total_triggers: int = 0
    successful_transfers: int = 0
    failed_transfers: int = 0

    class Config:
        from_attributes = True