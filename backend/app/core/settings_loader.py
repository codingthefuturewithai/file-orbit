"""
Settings loader that merges environment config with database settings.
This allows services to use the latest settings from the database.
"""
from typing import Dict, Any, Optional
from app.core.config import settings as base_settings
from app.core.database import AsyncSessionLocal
from app.services.settings_service import SettingsService
import asyncio
import logging

logger = logging.getLogger(__name__)


class SettingsLoader:
    """Loads and caches settings from database, falling back to config."""
    
    _cached_settings: Optional[Dict[str, Any]] = None
    _cache_timestamp: Optional[float] = None
    _cache_ttl: int = 300  # 5 minutes
    
    @classmethod
    async def get_settings(cls) -> Dict[str, Any]:
        """
        Get merged settings from config and database.
        Returns a dictionary of settings that can override config values.
        """
        import time
        
        # Check cache
        if cls._cached_settings and cls._cache_timestamp:
            if time.time() - cls._cache_timestamp < cls._cache_ttl:
                return cls._cached_settings
        
        try:
            async with AsyncSessionLocal() as db:
                db_settings = await SettingsService.get_settings_as_config(db)
                
            # Merge with base settings
            merged_settings = {}
            
            # Copy all base settings
            for attr in dir(base_settings):
                if not attr.startswith('_') and attr.isupper():
                    merged_settings[attr] = getattr(base_settings, attr)
            
            # Override with database settings
            merged_settings.update(db_settings)
            
            # Update cache
            cls._cached_settings = merged_settings
            cls._cache_timestamp = time.time()
            
            return merged_settings
            
        except Exception as e:
            logger.warning(f"Failed to load settings from database: {e}")
            # Fall back to base settings
            return {
                attr: getattr(base_settings, attr)
                for attr in dir(base_settings)
                if not attr.startswith('_') and attr.isupper()
            }
    
    @classmethod
    def invalidate_cache(cls):
        """Invalidate the settings cache."""
        cls._cached_settings = None
        cls._cache_timestamp = None
    
    @classmethod
    async def get_setting(cls, key: str, default: Any = None) -> Any:
        """Get a specific setting value."""
        settings = await cls.get_settings()
        return settings.get(key, default)


# Convenience function for sync code
def get_settings_sync() -> Dict[str, Any]:
    """Get settings synchronously (creates new event loop if needed)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, we can't use run_until_complete
            # Return base settings as fallback
            return {
                attr: getattr(base_settings, attr)
                for attr in dir(base_settings)
                if not attr.startswith('_') and attr.isupper()
            }
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(SettingsLoader.get_settings())