from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class SettingBase(BaseModel):
    """Base schema for settings."""
    key: str = Field(..., description="Unique key for the setting")
    value: Any = Field(..., description="Setting value (can be string, number, boolean, or JSON)")
    description: Optional[str] = Field(None, description="Human-readable description")
    category: Optional[str] = Field(None, description="Category for grouping settings")
    value_type: str = Field("string", description="Type hint: string, number, boolean, json")
    default_value: Optional[Any] = Field(None, description="Default value for reset functionality")
    is_visible: bool = Field(True, description="Whether to show in UI")
    is_editable: bool = Field(True, description="Whether users can edit this setting")


class SettingCreate(SettingBase):
    """Schema for creating a setting."""
    pass


class SettingUpdate(BaseModel):
    """Schema for updating a setting."""
    value: Any = Field(..., description="New value for the setting")
    updated_by: Optional[str] = Field(None, description="User or system that made the update")


class SettingInDB(SettingBase):
    """Schema for settings stored in database."""
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    version: int = 1
    previous_value: Optional[Any] = None
    
    class Config:
        from_attributes = True


class Setting(SettingInDB):
    """Schema for settings returned to API."""
    typed_value: Any = Field(None, description="Value with proper type conversion")
    
    class Config:
        from_attributes = True


class SettingBulkUpdate(BaseModel):
    """Schema for bulk updating multiple settings."""
    settings: Dict[str, Any] = Field(..., description="Dictionary of key-value pairs to update")
    updated_by: Optional[str] = Field(None, description="User or system that made the update")


class SettingCategory(BaseModel):
    """Schema for grouping settings by category."""
    category: str
    settings: list[Setting]
    
    
class SettingsResponse(BaseModel):
    """Response schema for all settings grouped by category."""
    categories: list[SettingCategory]
    total_settings: int