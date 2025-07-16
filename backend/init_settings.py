#!/usr/bin/env python3
"""
Initialize application settings in the database.
Run this after init_db.py to populate settings with default values.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import our app
sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.services.settings_service import SettingsService

async def init_settings():
    """Initialize settings with default values."""
    print("Initializing application settings...")
    
    async with AsyncSessionLocal() as db:
        await SettingsService.initialize_settings(db)
    
    print("Settings initialized successfully!")
    print("\nSettings categories created:")
    print("- email (SMTP configuration)")
    print("- throttling (Transfer rate limits)")
    print("- monitoring (Event monitoring)")
    print("- aws (AWS/S3 configuration)")
    print("- file_watch (Directory watching)")
    print("- general (General application settings)")

if __name__ == "__main__":
    asyncio.run(init_settings())