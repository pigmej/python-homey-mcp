"""Pytest configuration and fixtures for HomeyPro MCP Server tests."""

import os
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically set up test environment variables for all tests."""
    with patch.dict(
        os.environ,
        {
            "HOMEY_API_URL": "http://test.local",
            "HOMEY_API_TOKEN": "test_token_12345678901234567890",
            "HOMEY_TIMEOUT": "30.0",
            "HOMEY_VERIFY_SSL": "false",
            "HOMEY_CACHE_TTL": "300",
            "HOMEY_MAX_PAGE_SIZE": "100", 
            "HOMEY_DEFAULT_PAGE_SIZE": "25",
            "HOMEY_LOG_LEVEL": "DEBUG",
        },
        clear=False,
    ):
        yield


@pytest.fixture
def mock_homey_client():
    """Create a mock HomeyPro client for testing."""
    from unittest.mock import AsyncMock, MagicMock
    
    client = AsyncMock()
    
    # Mock device API
    client.devices = AsyncMock()
    client.devices.get_devices = AsyncMock(return_value=[])
    client.devices.get_device = AsyncMock()
    client.devices.get_device_capabilities = AsyncMock(return_value={})
    client.devices.get_device_settings = AsyncMock(return_value={})
    client.devices.get_device_classes = AsyncMock(return_value=[])
    client.devices.get_device_capabilities_list = AsyncMock(return_value=[])
    
    # Mock flows API
    client.flows = AsyncMock()
    client.flows.get_flows = AsyncMock(return_value=[])
    client.flows.get_advanced_flows = AsyncMock(return_value=[])
    client.flows.get_enabled_flows = AsyncMock(return_value=[])
    client.flows.get_disabled_flows = AsyncMock(return_value=[])
    client.flows.get_enabled_advanced_flows = AsyncMock(return_value=[])
    client.flows.get_disabled_advanced_flows = AsyncMock(return_value=[])
    
    # Mock zones API
    client.zones = AsyncMock()
    client.zones.get_zones = AsyncMock(return_value=[])
    
    # Mock system API
    client.system = AsyncMock()
    system_config = MagicMock()
    system_config.address = "Test Address"
    system_config.language = "en"
    system_config.units = "metric"
    system_config.is_metric.return_value = True
    system_config.get_location_coordinates.return_value = (51.5074, -0.1278)
    client.system.get_system_config = AsyncMock(return_value=system_config)
    
    return client


@pytest.fixture
def mock_ensure_client(mock_homey_client):
    """Mock the ensure_client function to return our test client."""
    with patch('homey_mcp.client.manager.ensure_client', return_value=mock_homey_client):
        yield mock_homey_client
