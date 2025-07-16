"""
API endpoints for managing application settings.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.settings_service import SettingsService
from app.schemas.settings import (
    Setting,
    SettingUpdate,
    SettingBulkUpdate,
    SettingCategory,
    SettingsResponse
)

router = APIRouter()


@router.get("/", response_model=SettingsResponse)
async def get_all_settings(
    db: AsyncSession = Depends(get_db)
) -> SettingsResponse:
    """Get all settings grouped by category."""
    settings = await SettingsService.get_all_settings(db)
    
    # Group by category
    categories_dict: Dict[str, List[Setting]] = {}
    for setting in settings:
        category = setting.category or "general"
        if category not in categories_dict:
            categories_dict[category] = []
        categories_dict[category].append(Setting.from_orm(setting))
    
    # Convert to response format
    categories = [
        SettingCategory(category=cat, settings=settings_list)
        for cat, settings_list in sorted(categories_dict.items())
    ]
    
    return SettingsResponse(
        categories=categories,
        total_settings=len(settings)
    )


@router.get("/category/{category}", response_model=List[Setting])
async def get_settings_by_category(
    category: str,
    db: AsyncSession = Depends(get_db)
) -> List[Setting]:
    """Get all settings for a specific category."""
    settings = await SettingsService.get_settings_by_category(db, category)
    return [Setting.from_orm(s) for s in settings]


@router.get("/{key}", response_model=Setting)
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db)
) -> Setting:
    """Get a specific setting by key."""
    setting = await SettingsService.get_setting(db, key)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting not found: {key}"
        )
    return Setting.from_orm(setting)


@router.put("/{key}", response_model=Setting)
async def update_setting(
    key: str,
    setting_update: SettingUpdate,
    db: AsyncSession = Depends(get_db)
) -> Setting:
    """Update a specific setting."""
    setting = await SettingsService.update_setting(
        db, 
        key, 
        setting_update.value,
        setting_update.updated_by or "api"
    )
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting not found or not editable: {key}"
        )
    return Setting.from_orm(setting)


@router.post("/bulk-update", response_model=Dict[str, bool])
async def bulk_update_settings(
    bulk_update: SettingBulkUpdate,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, bool]:
    """Update multiple settings at once."""
    results = await SettingsService.bulk_update_settings(
        db,
        bulk_update.settings,
        bulk_update.updated_by or "api"
    )
    return results


@router.post("/{key}/reset", response_model=Setting)
async def reset_setting(
    key: str,
    db: AsyncSession = Depends(get_db)
) -> Setting:
    """Reset a setting to its default value."""
    setting = await SettingsService.reset_setting(db, key)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting not found: {key}"
        )
    return Setting.from_orm(setting)


@router.post("/reset-all", response_model=Dict[str, Any])
async def reset_all_settings(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Reset all settings to their default values."""
    count = await SettingsService.reset_all_settings(db)
    return {
        "message": f"Reset {count} settings to default values",
        "count": count
    }


@router.post("/initialize", response_model=Dict[str, str])
async def initialize_settings(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Initialize settings with default values (admin only)."""
    await SettingsService.initialize_settings(db)
    return {"message": "Settings initialized successfully"}