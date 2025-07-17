"""
Test configuration and fixtures for backend tests.
"""
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.core.database import Base, get_db
from app.services.redis_manager import redis_manager


# Override database URL for testing
# Use the local postgres user for testing
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://timkitchens@localhost:5432/file_orbit_test"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        pool_size=5,
        max_overflow=10,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session override."""
    
    async def override_get_db():
        yield db_session
    
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Initialize Redis for tests
    await redis_manager.connect()
    
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()
    await redis_manager.disconnect()


@pytest.fixture
def test_data_dir(tmp_path):
    """Create temporary directory for test data."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def mock_rclone_config(tmp_path):
    """Create a mock rclone configuration file."""
    config_file = tmp_path / "rclone.conf"
    config_file.write_text("""
[test_s3]
type = s3
provider = AWS
access_key_id = test_key
secret_access_key = test_secret
region = us-east-1

[test_local]
type = local

[test_smb]
type = smb
host = test.local
user = testuser
pass = testpass
domain = WORKGROUP

[test_sftp]
type = sftp
host = test.local
user = testuser
pass = testpass
port = 22
""")
    return str(config_file)


@pytest.fixture
def sample_endpoint_data():
    """Sample endpoint data for testing."""
    return {
        "s3_endpoint": {
            "name": "Test S3",
            "type": "s3",
            "config": {
                "type": "s3",
                "provider": "AWS",
                "access_key_id": "test_key",
                "secret_access_key": "test_secret",
                "region": "us-east-1"
            }
        },
        "local_endpoint": {
            "name": "Test Local",
            "type": "local",
            "config": {
                "type": "local",
                "path": "/tmp/test"
            }
        },
        "smb_endpoint": {
            "name": "Test SMB",
            "type": "smb",
            "config": {
                "type": "smb",
                "host": "192.168.1.100",
                "user": "testuser",
                "pass": "testpass",
                "domain": "WORKGROUP"
            }
        },
        "sftp_endpoint": {
            "name": "Test SFTP",
            "type": "sftp",
            "config": {
                "type": "sftp",
                "host": "sftp.example.com",
                "user": "testuser",
                "pass": "testpass",
                "port": 22
            }
        }
    }


@pytest.fixture
def sample_job_data():
    """Sample job data for testing."""
    return {
        "name": "Test Transfer",
        "source_path": "/source/path",
        "destination_path": "/dest/path",
        "file_pattern": "*.mp4",
        "transfer_mode": "copy",
        "verify_checksum": True,
        "preserve_timestamps": True,
        "delete_after_transfer": False,
        "is_enabled": True
    }


@pytest_asyncio.fixture
async def db(db_session):
    """Alias for db_session to match test expectations"""
    yield db_session


@pytest.fixture
def sample_template_data():
    """Sample template data for testing."""
    return {
        "name": "Test Template",
        "description": "Test transfer template",
        "source_path": "/template/source",
        "destination_path": "/template/dest",
        "file_pattern": "*.mp4",
        "transfer_mode": "copy",
        "schedule_enabled": False,
        "event_trigger_enabled": False,
        "settings": {
            "verify_checksum": True,
            "preserve_timestamps": True,
            "delete_after_transfer": False
        }
    }