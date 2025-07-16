# Backend Tests

This directory contains the test suite for the FileOrbit backend API.

## Setup

### Database Setup

The tests require a PostgreSQL database. By default, tests use a separate test database to avoid affecting development data.

1. Create the test database:
```bash
psql -U $USER -h localhost -d postgres -c "CREATE DATABASE file_orbit_test;"
```

2. The test database URL is configured in `conftest.py`:
```python
TEST_DATABASE_URL = "postgresql+asyncpg://timkitchens@localhost:5432/file_orbit_test"
```

You can override this by setting the `TEST_DATABASE_URL` environment variable.

### Running Tests

1. Activate the virtual environment:
```bash
source venv/bin/activate
```

2. Run all tests:
```bash
python -m pytest
```

3. Run specific test file:
```bash
python -m pytest tests/test_settings_api.py
```

4. Run with verbose output:
```bash
python -m pytest -v
```

5. Run a specific test:
```bash
python -m pytest tests/test_settings_api.py::test_initialize_settings -v
```

## Test Structure

### conftest.py

Contains pytest fixtures used across all tests:

- `event_loop`: Async event loop for the test session
- `test_engine`: Test database engine that creates/drops tables
- `db_session`: Database session for each test (with automatic rollback)
- `client`: HTTP test client with database session override
- `test_data_dir`: Temporary directory for test files
- `mock_rclone_config`: Mock rclone configuration
- `sample_endpoint_data`: Sample endpoint configurations
- `sample_job_data`: Sample job data
- `sample_template_data`: Sample template data

### Test Files

- `test_settings_api.py`: Tests for the settings management API endpoints

## Writing Tests

1. All async tests should be marked with `@pytest.mark.asyncio`
2. Use the `client` fixture for API requests
3. Use the `db_session` fixture for direct database operations
4. Tests are automatically rolled back after each test

Example test:
```python
@pytest.mark.asyncio
async def test_example(client: AsyncClient, db_session: AsyncSession):
    # Make API request
    response = await client.get("/api/v1/endpoint")
    assert response.status_code == 200
    
    # Direct database query if needed
    result = await db_session.execute(select(Model))
    assert result is not None
```

## Known Issues

- Some Pydantic V2 deprecation warnings appear in test output (these don't affect functionality)
- Redis deprecation warning for `close()` method (should use `aclose()`)

## Test Database Cleanup

The test database tables are automatically created before tests and dropped after all tests complete. Each individual test runs in a transaction that is rolled back, ensuring test isolation.