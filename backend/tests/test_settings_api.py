import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import Settings, SETTING_KEYS
from app.services.settings_service import SettingsService


@pytest.mark.asyncio
async def test_initialize_settings(client: AsyncClient, db_session: AsyncSession):
    """Test that settings can be initialized."""
    response = await client.post("/api/v1/settings/initialize")
    assert response.status_code == 200
    
    # Verify settings were created
    settings = await SettingsService.get_all_settings(db_session)
    assert len(settings) > 0
    
    # Check that all predefined keys exist
    setting_keys = {s.key for s in settings}
    assert set(SETTING_KEYS.keys()).issubset(setting_keys)


@pytest.mark.asyncio
async def test_get_all_settings(client: AsyncClient, db_session: AsyncSession):
    """Test getting all settings grouped by category."""
    # Initialize settings first
    await SettingsService.initialize_settings(db_session)
    
    response = await client.get("/api/v1/settings/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    assert "categories" in data
    assert "total_settings" in data
    
    # Check that categories is a list
    categories = data["categories"]
    assert isinstance(categories, list)
    assert len(categories) > 0
    
    # Check category structure
    for category in categories:
        assert "category" in category
        assert "settings" in category
        assert isinstance(category["settings"], list)
        
    # Check that we have expected categories
    category_names = [c["category"] for c in categories]
    assert "general" in category_names
    assert "email" in category_names
    assert "throttling" in category_names


@pytest.mark.asyncio
async def test_get_settings_by_category(client: AsyncClient, db_session: AsyncSession):
    """Test getting settings by specific category."""
    await SettingsService.initialize_settings(db_session)
    
    response = await client.get("/api/v1/settings/category/general")
    assert response.status_code == 200
    
    settings = response.json()
    assert isinstance(settings, list)
    assert all(s["category"] == "general" for s in settings)


@pytest.mark.asyncio
async def test_get_single_setting(client: AsyncClient, db_session: AsyncSession):
    """Test getting a single setting by key."""
    await SettingsService.initialize_settings(db_session)
    
    response = await client.get("/api/v1/settings/general.log_level")
    assert response.status_code == 200
    
    setting = response.json()
    assert setting["key"] == "general.log_level"
    assert setting["value"] == "info"


@pytest.mark.asyncio
async def test_update_setting(client: AsyncClient, db_session: AsyncSession):
    """Test updating a setting value."""
    await SettingsService.initialize_settings(db_session)
    
    # Update log level
    response = await client.put(
        "/api/v1/settings/general.log_level",
        json={"value": "debug"}
    )
    assert response.status_code == 200
    
    updated = response.json()
    assert updated["key"] == "general.log_level"
    assert updated["value"] == "debug"
    assert updated["version"] == 2  # Version should increment


@pytest.mark.asyncio
async def test_bulk_update_settings(client: AsyncClient, db_session: AsyncSession):
    """Test bulk updating multiple settings."""
    await SettingsService.initialize_settings(db_session)
    
    updates = {
        "general.log_level": "warning",
        "general.max_log_size_mb": 200,
        "throttling.default_max_concurrent": 10
    }
    
    # Use correct schema with 'settings' field
    response = await client.post(
        "/api/v1/settings/bulk-update",
        json={"settings": updates}
    )
    assert response.status_code == 200
    
    results = response.json()
    assert all(results.values())  # All updates should succeed
    
    # Verify updates
    for key, value in updates.items():
        setting = await SettingsService.get_setting(db_session, key)
        assert setting.value == value


@pytest.mark.asyncio
async def test_reset_setting(client: AsyncClient, db_session: AsyncSession):
    """Test resetting a setting to default value."""
    await SettingsService.initialize_settings(db_session)
    
    # First update a setting
    await client.put(
        "/api/v1/settings/general.log_level",
        json={"value": "debug"}
    )
    
    # Then reset it
    response = await client.post("/api/v1/settings/general.log_level/reset")
    assert response.status_code == 200
    
    reset_setting = response.json()
    assert reset_setting["value"] == "info"  # Back to default


@pytest.mark.asyncio
async def test_reset_all_settings(client: AsyncClient, db_session: AsyncSession):
    """Test resetting all settings to defaults."""
    await SettingsService.initialize_settings(db_session)
    
    # Update some settings
    updates = {
        "general.log_level": "warning",
        "throttling.default_max_concurrent": 20
    }
    await client.post("/api/v1/settings/bulk-update", json={"settings": updates})
    
    # Reset all
    response = await client.post("/api/v1/settings/reset-all")
    assert response.status_code == 200
    
    # Verify all are back to defaults
    setting1 = await SettingsService.get_setting(db_session, "general.log_level")
    assert setting1.value == "info"
    
    setting2 = await SettingsService.get_setting(db_session, "throttling.default_max_concurrent")
    assert setting2.value == 5


@pytest.mark.asyncio
async def test_setting_encryption(client: AsyncClient, db_session: AsyncSession):
    """Test that sensitive settings are encrypted in database."""
    await SettingsService.initialize_settings(db_session)
    
    # Update a password field
    password = "super-secret-password"
    response = await client.put(
        "/api/v1/settings/email.smtp_password",
        json={"value": password}
    )
    assert response.status_code == 200
    
    # Check that the raw value in DB is not the password
    # (it should be encrypted)
    from app.models.settings import Settings as SettingsModel
    from sqlalchemy import select
    
    result = await db_session.execute(
        select(SettingsModel).where(SettingsModel.key == "email.smtp_password")
    )
    db_setting = result.scalar_one_or_none()
    assert db_setting is not None
    
    # The stored value should be different from the original password
    # (encrypted values are typically longer and base64 encoded)
    assert db_setting.value != password
    assert isinstance(db_setting.value, str)
    
    # But API should return decrypted value in typed_value field
    response = await client.get("/api/v1/settings/email.smtp_password")
    setting_data = response.json()
    # The 'value' field contains the encrypted value
    assert setting_data["value"] != password
    # The 'typed_value' field should contain the decrypted value
    assert setting_data["typed_value"] == password


@pytest.mark.asyncio
async def test_setting_type_validation(client: AsyncClient, db_session: AsyncSession):
    """Test setting value type handling."""
    await SettingsService.initialize_settings(db_session)
    
    # Update a number setting with a valid number
    response = await client.put(
        "/api/v1/settings/general.max_log_size_mb",
        json={"value": 500}
    )
    assert response.status_code == 200
    
    # The service should handle type conversion appropriately
    setting = await SettingsService.get_setting(db_session, "general.max_log_size_mb")
    assert setting.value == 500


@pytest.mark.asyncio
async def test_nonexistent_setting(client: AsyncClient):
    """Test accessing a setting that doesn't exist."""
    response = await client.get("/api/v1/settings/nonexistent.setting")
    assert response.status_code == 404
    
    response = await client.put(
        "/api/v1/settings/nonexistent.setting",
        json={"value": "test"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_setting_visibility(client: AsyncClient, db_session: AsyncSession):
    """Test that non-visible settings are still accessible via API."""
    await SettingsService.initialize_settings(db_session)
    
    # SMTP password is marked as not visible
    response = await client.get("/api/v1/settings/email.smtp_password")
    assert response.status_code == 200
    
    setting = response.json()
    assert setting["is_visible"] is False
    # But value should still be returned (frontend decides how to handle visibility)