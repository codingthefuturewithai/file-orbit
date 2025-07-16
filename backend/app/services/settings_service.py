"""
Service for managing application settings stored in the database.
Handles initialization, updates, and synchronization with config.
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.settings import Settings, SETTING_KEYS
from app.core.config import settings as config_settings
from app.utils.encryption import encryption_service, should_encrypt_setting
import logging

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for managing persistent application settings."""
    
    @staticmethod
    async def initialize_settings(db: AsyncSession) -> None:
        """
        Initialize settings in the database with default values.
        Only creates settings that don't already exist.
        """
        for key, setting_config in SETTING_KEYS.items():
            # Check if setting already exists
            result = await db.execute(
                select(Settings).where(Settings.key == key)
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                # Get current value from config or use default
                current_value = SettingsService._get_config_value(key, setting_config["default_value"])
                
                # Encrypt sensitive values before storing
                value_to_store = current_value
                if should_encrypt_setting(key) and current_value:
                    value_to_store = encryption_service.encrypt(str(current_value))
                
                setting = Settings(
                    key=key,
                    value=value_to_store,
                    description=setting_config["description"],
                    category=setting_config["category"],
                    value_type=setting_config["value_type"],
                    default_value=setting_config["default_value"],
                    is_visible=setting_config.get("is_visible", True),
                    is_editable=setting_config.get("is_editable", True),
                    updated_by="system"
                )
                db.add(setting)
                logger.info(f"Initialized setting: {key}")
        
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            logger.warning("Some settings already exist, skipping initialization")
    
    @staticmethod
    async def get_all_settings(db: AsyncSession) -> List[Settings]:
        """Get all settings from the database."""
        result = await db.execute(select(Settings).order_by(Settings.category, Settings.key))
        return result.scalars().all()
    
    @staticmethod
    async def get_settings_by_category(db: AsyncSession, category: str) -> List[Settings]:
        """Get all settings for a specific category."""
        result = await db.execute(
            select(Settings)
            .where(Settings.category == category)
            .order_by(Settings.key)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_setting(db: AsyncSession, key: str) -> Optional[Settings]:
        """Get a specific setting by key."""
        result = await db.execute(
            select(Settings).where(Settings.key == key)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_setting(
        db: AsyncSession, 
        key: str, 
        value: Any, 
        updated_by: str = "user"
    ) -> Optional[Settings]:
        """Update a setting value."""
        setting = await SettingsService.get_setting(db, key)
        if not setting:
            logger.error(f"Setting not found: {key}")
            return None
        
        if not setting.is_editable:
            logger.warning(f"Attempted to update non-editable setting: {key}")
            return None
        
        # Store previous value for audit trail
        setting.previous_value = setting.value
        
        # Encrypt sensitive values before storing
        value_to_store = value
        if should_encrypt_setting(key) and value:
            value_to_store = encryption_service.encrypt(str(value))
        
        setting.value = value_to_store
        setting.updated_by = updated_by
        setting.version += 1
        
        await db.commit()
        await db.refresh(setting)
        
        logger.info(f"Updated setting {key}: {setting.previous_value} -> {value}")
        return setting
    
    @staticmethod
    async def bulk_update_settings(
        db: AsyncSession,
        updates: Dict[str, Any],
        updated_by: str = "user"
    ) -> Dict[str, bool]:
        """Update multiple settings at once."""
        results = {}
        
        for key, value in updates.items():
            setting = await SettingsService.update_setting(db, key, value, updated_by)
            results[key] = setting is not None
        
        return results
    
    @staticmethod
    async def reset_setting(db: AsyncSession, key: str) -> Optional[Settings]:
        """Reset a setting to its default value."""
        setting = await SettingsService.get_setting(db, key)
        if not setting:
            return None
        
        if setting.default_value is not None:
            return await SettingsService.update_setting(
                db, key, setting.default_value, "system"
            )
        return setting
    
    @staticmethod
    async def reset_all_settings(db: AsyncSession) -> int:
        """Reset all settings to their default values."""
        settings_list = await SettingsService.get_all_settings(db)
        count = 0
        
        for setting in settings_list:
            if setting.default_value is not None and setting.is_editable:
                await SettingsService.reset_setting(db, setting.key)
                count += 1
        
        return count
    
    @staticmethod
    def _get_config_value(key: str, default: Any) -> Any:
        """Get current value from config based on setting key."""
        # Map setting keys to config attributes
        key_mapping = {
            # Email
            "email.smtp_host": "SMTP_HOST",
            "email.smtp_port": "SMTP_PORT",
            "email.smtp_user": "SMTP_USER",
            "email.smtp_password": "SMTP_PASSWORD",
            "email.smtp_from": "SMTP_FROM",
            "email.smtp_tls": "SMTP_TLS",
            
            # Throttling
            "throttling.default_max_concurrent": "DEFAULT_MAX_CONCURRENT",
            "throttling.check_interval": "THROTTLE_CHECK_INTERVAL",
            
            # Monitoring
            "monitoring.enable_event_monitoring": "ENABLE_EVENT_MONITORING",
            "monitoring.event_poll_interval": "EVENT_POLL_INTERVAL",
            
            # AWS
            "aws.region": "AWS_REGION",
            "aws.access_key_id": "AWS_ACCESS_KEY_ID",
            "aws.secret_access_key": "AWS_SECRET_ACCESS_KEY",
            "aws.sqs_queue_url": "SQS_QUEUE_URL",
            
            # File watching
            "file_watch.directories": "WATCH_DIRECTORIES",
            
            # General
            "general.project_name": "PROJECT_NAME",
            "general.access_token_expire_minutes": "ACCESS_TOKEN_EXPIRE_MINUTES"
        }
        
        config_attr = key_mapping.get(key)
        if config_attr and hasattr(config_settings, config_attr):
            return getattr(config_settings, config_attr)
        
        return default
    
    @staticmethod
    async def get_settings_as_config(db: AsyncSession) -> Dict[str, Any]:
        """
        Get all settings as a dictionary suitable for overriding config values.
        This can be used by services to get the latest settings.
        """
        settings_list = await SettingsService.get_all_settings(db)
        config_dict = {}
        
        for setting in settings_list:
            # Use typed_value which handles decryption automatically
            # Convert database key format to config attribute format
            if setting.key.startswith("email."):
                prefix = "SMTP_"
                key_part = setting.key.replace("email.smtp_", "").upper()
                config_dict[f"{prefix}{key_part}"] = setting.typed_value
            elif setting.key.startswith("throttling."):
                if "default_max_concurrent" in setting.key:
                    config_dict["DEFAULT_MAX_CONCURRENT"] = setting.typed_value
                elif "check_interval" in setting.key:
                    config_dict["THROTTLE_CHECK_INTERVAL"] = setting.typed_value
            elif setting.key.startswith("monitoring."):
                if "enable_event_monitoring" in setting.key:
                    config_dict["ENABLE_EVENT_MONITORING"] = setting.typed_value
                elif "event_poll_interval" in setting.key:
                    config_dict["EVENT_POLL_INTERVAL"] = setting.typed_value
            elif setting.key.startswith("aws."):
                key_part = setting.key.replace("aws.", "").upper()
                if key_part == "REGION":
                    config_dict["AWS_REGION"] = setting.typed_value
                else:
                    config_dict[f"AWS_{key_part}"] = setting.typed_value
            elif setting.key == "file_watch.directories":
                config_dict["WATCH_DIRECTORIES"] = setting.typed_value
            elif setting.key.startswith("general."):
                if "project_name" in setting.key:
                    config_dict["PROJECT_NAME"] = setting.typed_value
                elif "access_token_expire_minutes" in setting.key:
                    config_dict["ACCESS_TOKEN_EXPIRE_MINUTES"] = setting.typed_value
        
        return config_dict