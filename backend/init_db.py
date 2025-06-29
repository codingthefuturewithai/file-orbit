#!/usr/bin/env python3
"""
Initialize the database by creating all tables.
Run this before starting the application for the first time.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import our app
sys.path.append(str(Path(__file__).parent))

from app.core.database import engine, Base
from app.models import Job, Transfer, Endpoint, TransferTemplate  # Import all models to register them

async def init_database():
    """Create all database tables"""
    print("Creating database tables...")
    
    async with engine.begin() as conn:
        # Drop all tables first (BE CAREFUL - this deletes all data!)
        await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database tables created successfully!")
    print("\nTables created:")
    print("- jobs")
    print("- transfers") 
    print("- endpoints")
    print("- transfer_templates")

if __name__ == "__main__":
    asyncio.run(init_database())