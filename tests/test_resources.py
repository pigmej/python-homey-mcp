"""Unit tests for resource functionality."""

import pytest
import pytest_asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import homey_mcp.tools.resources as resources_module
from homey_mcp.tools.resources import (
    CacheEntry,
    SimpleCache,
)

# Configure pytest-asyncio
pytest_asyncio.auto_mode = True


class TestCacheEntry:
    """Test CacheEntry data class."""
    
    def test_cache_entry_creation(self):
        """Test creating a CacheEntry instance."""
        data = {"test": "data"}
        timestamp = time.time()
        ttl = 300.0
        
        entry = CacheEntry(data, timestamp, ttl)
        
        assert entry.data == data
        assert entry.timestamp == timestamp
        assert entry.ttl == ttl
    
    def test_cache_entry_not_expired(self):
        """Test cache entry that has not expired."""
        data = {"test": "data"}
        timestamp = time.time()
        ttl = 300.0  # 5 minutes
        
        entry = CacheEntry(data, timestamp, ttl)
        
        assert not entry.is_expired()
    
    def test_cache_entry_expired(self):
        """Test cache entry that has expired."""
        data = {"test": "data"}
        timestamp = time.time() - 400  # 400 seconds ago
        ttl = 300.0  # 5 minutes TTL
        
        entry = CacheEntry(data, timestamp, ttl)
        
        assert entry.is_expired()


class TestSimpleCache:
    """Test SimpleCache class."""
    
    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = SimpleCache()
        assert cache._cache == {}
    
    async def test_cache_miss_fetch_success(self):
        """Test cache miss with successful fetch."""
        cache = SimpleCache()
        
        async def mock_fetcher():
            return {"data": "test_value"}
        
        result = await cache.get_or_fetch("test_key", mock_fetcher, 300)
        
        assert result == {"data": "test_value"}
        assert "test_key" in cache._cache
        assert cache._cache["test_key"].data == {"data": "test_value"}
    
    async def test_cache_hit(self):
        """Test cache hit with fresh data."""
        cache = SimpleCache()
        
        # Pre-populate cache with fresh data
        test_data = {"data": "cached_value"}
        cache._cache["test_key"] = CacheEntry(test_data, time.time(), 300)
        
        async def mock_fetcher():
            return {"data": "new_value"}  # Should not be called
        
        result = await cache.get_or_fetch("test_key", mock_fetcher, 300)
        
        assert result == test_data
    
    async def test_cache_expired_fetch_success(self):
        """Test expired cache with successful fetch."""
        cache = SimpleCache()
        
        # Pre-populate cache with expired data
        old_data = {"data": "old_value"}
        cache._cache["test_key"] = CacheEntry(old_data, time.time() - 400, 300)
        
        async def mock_fetcher():
            return {"data": "new_value"}
        
        result = await cache.get_or_fetch("test_key", mock_fetcher, 300)
        
        assert result == {"data": "new_value"}
        assert cache._cache["test_key"].data == {"data": "new_value"}
    
    async def test_cache_connection_error_with_stale_data(self):
        """Test connection error with stale data fallback."""
        cache = SimpleCache()
        
        # Pre-populate cache with expired data
        stale_data = {"data": "stale_value"}
        cache._cache["test_key"] = CacheEntry(stale_data, time.time() - 400, 300)
        
        async def mock_fetcher():
            raise ConnectionError("Connection failed")
        
        result = await cache.get_or_fetch("test_key", mock_fetcher, 300)
        
        assert result["data"] == stale_data
        assert result["is_stale"] is True
        assert result["error_type"] == "connection"
    
    async def test_cache_timeout_error_with_stale_data(self):
        """Test timeout error with stale data fallback."""
        cache = SimpleCache()
        
        # Pre-populate cache with expired data
        stale_data = {"data": "stale_value"}
        cache._cache["test_key"] = CacheEntry(stale_data, time.time() - 400, 300)
        
        async def mock_fetcher():
            raise TimeoutError("Request timed out")
        
        result = await cache.get_or_fetch("test_key", mock_fetcher, 300)
        
        assert result["data"] == stale_data
        assert result["is_stale"] is True
        assert result["error_type"] == "timeout"
    
    async def test_cache_generic_error_with_stale_data(self):
        """Test generic error with stale data fallback."""
        cache = SimpleCache()
        
        # Pre-populate cache with expired data
        stale_data = {"data": "stale_value"}
        cache._cache["test_key"] = CacheEntry(stale_data, time.time() - 400, 300)
        
        async def mock_fetcher():
            raise ValueError("Some error")
        
        result = await cache.get_or_fetch("test_key", mock_fetcher, 300)
        
        assert result["data"] == stale_data
        assert result["is_stale"] is True
        assert result["error_type"] == "unknown"
    
    async def test_cache_connection_error_no_stale_data(self):
        """Test connection error without stale data."""
        cache = SimpleCache()
        
        async def mock_fetcher():
            raise ConnectionError("Connection failed")
        
        with pytest.raises(ConnectionError):
            await cache.get_or_fetch("test_key", mock_fetcher, 300)
    
    async def test_cache_timeout_error_no_stale_data(self):
        """Test timeout error without stale data."""
        cache = SimpleCache()
        
        async def mock_fetcher():
            raise TimeoutError("Request timed out")
        
        with pytest.raises(TimeoutError):
            await cache.get_or_fetch("test_key", mock_fetcher, 300)
    
    async def test_cache_generic_error_no_stale_data(self):
        """Test generic error without stale data."""
        cache = SimpleCache()
        
        async def mock_fetcher():
            raise ValueError("Some error")
        
        with pytest.raises(ValueError):
            await cache.get_or_fetch("test_key", mock_fetcher, 300)


class TestSystemOverviewResource:
    """Test system_overview_resource function."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock client with sample data."""
        client = AsyncMock()
        
        # Mock system config
        mock_system_config = MagicMock()
        mock_system_config.name = "HomeyPro Test"
        mock_system_config.version = "10.0.0"
        mock_system_config.platform = "homey"
        mock_system_config.uptime = 86400
        
        client.system.get_system_config.return_value = mock_system_config
        
        # Mock devices
        mock_device1 = MagicMock()
        mock_device1.available = True
        mock_device1.class_ = "light"
        mock_device1.capabilities = {"onoff": True, "dim": 0.5}
        
        mock_device2 = MagicMock()
        mock_device2.available = False
        mock_device2.class_ = "sensor"
        mock_device2.capabilities = ["measure_temperature"]
        
        client.devices.get_devices.return_value = [mock_device1, mock_device2]
        
        # Mock zones
        mock_zone1 = MagicMock()
        mock_zone1.name = "Living Room"
        mock_zone2 = MagicMock()
        mock_zone2.name = "Kitchen"
        
        client.zones.get_zones.return_value = [mock_zone1, mock_zone2]
        
        return client
    
    @patch.dict('os.environ', {'HOMEY_API_URL': 'http://test.local', 'HOMEY_API_TOKEN': 'test_token'})
    @patch('homey_mcp.tools.resources.ensure_client')
    @patch('homey_mcp.tools.resources._resource_cache')
    async def test_system_overview_success(self, mock_cache, mock_ensure_client, mock_client):
        """Test successful system overview resource generation."""
        mock_ensure_client.return_value = mock_client
        
        # Mock cache to return fresh data
        expected_data = {
            "device_summary": {
                "total_count": 2,
                "online_count": 1,
                "offline_count": 1,
                "device_types_count": 2,
                "capabilities_count": 3,
                "health_percentage": 50.0
            },
            "zone_summary": {
                "total_count": 2,
                "zone_names": ["Living Room", "Kitchen"]
            }
        }
        mock_cache.get_or_fetch = AsyncMock(return_value=expected_data)
        
        result = await resources_module.system_overview_resource.fn()
        
        assert isinstance(result, dict)
        assert result == expected_data
        mock_cache.get_or_fetch.assert_called_once()
    
    @patch.dict('os.environ', {'HOMEY_API_URL': 'http://test.local', 'HOMEY_API_TOKEN': 'test_token'})
    @patch('homey_mcp.tools.resources.ensure_client')
    @patch('homey_mcp.tools.resources._resource_cache')
    async def test_system_overview_stale_data(self, mock_cache, mock_ensure_client):
        """Test system overview resource with stale data."""
        mock_ensure_client.return_value = AsyncMock()
        
        # Mock cache to return stale data
        stale_response = {
            "data": {"system_info": {"name": "Test"}, "cache_info": {}},
            "is_stale": True,
            "error_type": "connection"
        }
        mock_cache.get_or_fetch = AsyncMock(return_value=stale_response)
        
        result = await resources_module.system_overview_resource.fn()
        
        assert isinstance(result, dict)
        assert "cache_info" in result
        assert result["cache_info"]["is_stale"] is True
        assert result["cache_info"]["error_type"] == "connection"
    
    @patch.dict('os.environ', {'HOMEY_API_URL': 'http://test.local', 'HOMEY_API_TOKEN': 'test_token'})
    @patch('homey_mcp.tools.resources.ensure_client')
    @patch('homey_mcp.tools.resources._resource_cache')
    async def test_system_overview_connection_error(self, mock_cache, mock_ensure_client):
        """Test system overview resource with connection error."""
        mock_ensure_client.return_value = AsyncMock()
        mock_cache.get_or_fetch.side_effect = ConnectionError("Connection failed")
        
        result = await resources_module.system_overview_resource.fn()
        
        assert isinstance(result, dict)
        assert "connection issues" in result["error"]
        assert result["error_type"] == "connection"
    
    @patch.dict('os.environ', {'HOMEY_API_URL': 'http://test.local', 'HOMEY_API_TOKEN': 'test_token'})
    @patch('homey_mcp.tools.resources.ensure_client')
    @patch('homey_mcp.tools.resources._resource_cache')
    async def test_system_overview_timeout_error(self, mock_cache, mock_ensure_client):
        """Test system overview resource with timeout error."""
        mock_ensure_client.return_value = AsyncMock()
        mock_cache.get_or_fetch.side_effect = TimeoutError("Request timed out")
        
        result = await resources_module.system_overview_resource.fn()
        
        assert isinstance(result, dict)
        assert "timeout" in result["error"]
        assert result["error_type"] == "timeout"
    
    @patch('homey_mcp.tools.resources.ensure_client')
    @patch('homey_mcp.tools.resources._resource_cache')
    async def test_system_overview_generic_error(self, mock_cache, mock_ensure_client):
        """Test system overview resource with generic error."""
        mock_ensure_client.return_value = AsyncMock()
        mock_cache.get_or_fetch.side_effect = ValueError("Some error")
        
        result = await resources_module.system_overview_resource.fn()
        
        assert isinstance(result, dict)
        assert "unexpected error" in result["error"]
        assert result["error_type"] == "unknown"


class TestDeviceRegistryResource:
    """Test device_registry_resource function."""
    
    @pytest.fixture
    def mock_client_with_devices(self):
        """Create a mock client with device data."""
        client = AsyncMock()
        
        # Mock devices with various states
        mock_device1 = MagicMock()
        mock_device1.id = "device1"
        mock_device1.name = "Living Room Light"
        mock_device1.zone = "zone1"
        mock_device1.class_ = "light"
        mock_device1.available = True
        mock_device1.capabilities = {"onoff": True, "dim": 0.8}
        mock_device1.energy = {"batteries": ["INTERNAL"]}
        mock_device1.settings = {"duration": 5}
        mock_device1.ui = {"quickAction": "onoff"}
        
        # Mock capability objects
        mock_cap_obj = MagicMock()
        mock_cap_obj.value = True
        mock_device1.capabilitiesObj = {"onoff": mock_cap_obj}
        
        mock_device2 = MagicMock()
        mock_device2.id = "device2"
        mock_device2.name = "Temperature Sensor"
        mock_device2.zone = "zone1"
        mock_device2.class_ = "sensor"
        mock_device2.available = False
        mock_device2.capabilities = ["measure_temperature", "alarm_battery"]
        mock_device2.energy = None
        mock_device2.settings = {}
        mock_device2.ui = {}
        mock_device2.capabilitiesObj = {}
        
        client.devices.get_devices.return_value = [mock_device1, mock_device2]
        
        return client
    
    @patch.dict('os.environ', {'HOMEY_API_URL': 'http://test.local', 'HOMEY_API_TOKEN': 'test_token'})
    @patch('homey_mcp.tools.resources.ensure_client')
    @patch('homey_mcp.tools.resources._resource_cache')
    async def test_device_registry_success(self, mock_cache, mock_ensure_client, mock_client_with_devices):
        """Test successful device registry resource generation."""
        mock_ensure_client.return_value = mock_client_with_devices
        
        # Mock cache to return fresh data
        expected_data = {
            "devices": [
                {
                    "id": "device1",
                    "name": "Living Room Light",
                    "zone": "zone1",
                    "class": "light",
                    "available": True,
                    "capabilities": {"onoff": True, "dim": 0.8},
                    "capability_values": {"onoff": True}
                },
                {
                    "id": "device2",
                    "name": "Temperature Sensor",
                    "zone": "zone1",
                    "class": "sensor",
                    "available": False,
                    "capabilities": {"measure_temperature": True, "alarm_battery": True},
                    "capability_values": {}
                }
            ],
            "summary": {
                "total_count": 2,
                "online_count": 1,
                "offline_count": 1,
                "device_types": ["light", "sensor"],
                "capabilities": ["onoff", "dim", "measure_temperature", "alarm_battery"]
            }
        }
        mock_cache.get_or_fetch = AsyncMock(return_value=expected_data)
        
        result = await resources_module.device_registry_resource.fn()
        
        assert isinstance(result, dict)
        assert result == expected_data
        mock_cache.get_or_fetch.assert_called_once()
    
    @patch.dict('os.environ', {'HOMEY_API_URL': 'http://test.local', 'HOMEY_API_TOKEN': 'test_token'})
    @patch('homey_mcp.tools.resources.ensure_client')
    @patch('homey_mcp.tools.resources._resource_cache')
    async def test_device_registry_connection_error(self, mock_cache, mock_ensure_client):
        """Test device registry resource with connection error."""
        mock_ensure_client.return_value = AsyncMock()
        mock_cache.get_or_fetch.side_effect = ConnectionError("Connection failed")
        
        result = await resources_module.device_registry_resource.fn()
        
        assert isinstance(result, dict)
        assert "connection issues" in result["error"]
        assert result["error_type"] == "connection"


class TestZoneHierarchyResource:
    """Test zone_hierarchy_resource function."""
    
    @pytest.fixture
    def mock_client_with_zones(self):
        """Create a mock client with zone and device data."""
        client = AsyncMock()
        
        # Mock zones
        mock_zone1 = MagicMock()
        mock_zone1.id = "zone1"
        mock_zone1.name = "Living Room"
        mock_zone1.parent = None
        mock_zone1.active = True
        mock_zone1.icon = "room"
        
        mock_zone2 = MagicMock()
        mock_zone2.id = "zone2"
        mock_zone2.name = "Kitchen"
        mock_zone2.parent = "zone1"
        mock_zone2.active = True
        mock_zone2.icon = "kitchen"
        
        client.zones.get_zones.return_value = [mock_zone1, mock_zone2]
        
        # Mock devices
        mock_device1 = MagicMock()
        mock_device1.id = "device1"
        mock_device1.name = "Living Room Light"
        mock_device1.zone = "zone1"
        mock_device1.class_ = "light"
        mock_device1.available = True
        
        mock_device2 = MagicMock()
        mock_device2.id = "device2"
        mock_device2.name = "Kitchen Light"
        mock_device2.zone = "zone2"
        mock_device2.class_ = "light"
        mock_device2.available = False
        
        client.devices.get_devices.return_value = [mock_device1, mock_device2]
        
        return client
    
    @patch.dict('os.environ', {'HOMEY_API_URL': 'http://test.local', 'HOMEY_API_TOKEN': 'test_token'})
    @patch('homey_mcp.tools.resources.ensure_client')
    @patch('homey_mcp.tools.resources._resource_cache')
    async def test_zone_hierarchy_success(self, mock_cache, mock_ensure_client, mock_client_with_zones):
        """Test successful zone hierarchy resource generation."""
        mock_ensure_client.return_value = mock_client_with_zones
        
        # Mock cache to return fresh data
        expected_data = {
            "zones": [
                {
                    "id": "zone1",
                    "name": "Living Room",
                    "parent": None,
                    "active": True,
                    "icon": "room",
                    "devices": [{"id": "device1", "name": "Living Room Light", "class": "light", "available": True}],
                    "device_count": 1,
                    "online_device_count": 1,
                    "type": "room",
                    "children": ["zone2"]
                },
                {
                    "id": "zone2",
                    "name": "Kitchen",
                    "parent": "zone1",
                    "active": True,
                    "icon": "kitchen",
                    "devices": [{"id": "device2", "name": "Kitchen Light", "class": "light", "available": False}],
                    "device_count": 1,
                    "online_device_count": 0,
                    "type": "kitchen"
                }
            ],
            "summary": {
                "total_zones": 2,
                "zones_with_devices": 2,
                "total_devices_assigned": 2,
                "zone_types": ["room", "kitchen"]
            }
        }
        mock_cache.get_or_fetch = AsyncMock(return_value=expected_data)
        
        result = await resources_module.zone_hierarchy_resource.fn()
        
        assert isinstance(result, dict)
        assert result == expected_data
        mock_cache.get_or_fetch.assert_called_once()
    
    @patch.dict('os.environ', {'HOMEY_API_URL': 'http://test.local', 'HOMEY_API_TOKEN': 'test_token'})
    @patch('homey_mcp.tools.resources.ensure_client')
    @patch('homey_mcp.tools.resources._resource_cache')
    async def test_zone_hierarchy_timeout_error(self, mock_cache, mock_ensure_client):
        """Test zone hierarchy resource with timeout error."""
        mock_ensure_client.return_value = AsyncMock()
        mock_cache.get_or_fetch.side_effect = TimeoutError("Request timed out")
        
        result = await resources_module.zone_hierarchy_resource.fn()
        
        assert isinstance(result, dict)
        assert "timeout" in result["error"]
        assert result["error_type"] == "timeout"


class TestFlowCatalogResource:
    """Test flow_catalog_resource function."""
    
    @pytest.fixture
    def mock_client_with_flows(self):
        """Create a mock client with flow data."""
        client = AsyncMock()
        
        # Mock flows
        mock_flow1 = MagicMock()
        mock_flow1.id = "flow1"
        mock_flow1.name = "Morning Routine"
        mock_flow1.enabled = True
        mock_flow1.folder = None
        mock_flow1.type = "normal"
        mock_flow1.broken = False
        mock_flow1.lastExecuted = "2024-01-01T08:00:00Z"
        
        # Mock trigger
        mock_trigger = MagicMock()
        mock_trigger.id = "trigger1"
        mock_trigger.uri = "homey:manager:cron"
        mock_trigger.title = "Time Trigger"
        mock_flow1.trigger = mock_trigger
        
        # Mock conditions and actions
        mock_condition = MagicMock()
        mock_condition.id = "condition1"
        mock_condition.uri = "homey:manager:logic"
        mock_condition.title = "Logic Condition"
        mock_flow1.conditions = [mock_condition]
        
        mock_action = MagicMock()
        mock_action.id = "action1"
        mock_action.uri = "homey:device:control"
        mock_action.title = "Device Action"
        mock_flow1.actions = [mock_action]
        
        mock_flow2 = MagicMock()
        mock_flow2.id = "flow2"
        mock_flow2.name = "Security Alert"
        mock_flow2.enabled = False
        mock_flow2.folder = "security"
        mock_flow2.type = "normal"
        mock_flow2.broken = True
        mock_flow2.lastExecuted = None
        mock_flow2.trigger = None
        mock_flow2.conditions = []
        mock_flow2.actions = []
        
        client.flows.get_flows.return_value = [mock_flow1, mock_flow2]
        
        return client
    
    @patch.dict('os.environ', {'HOMEY_API_URL': 'http://test.local', 'HOMEY_API_TOKEN': 'test_token'})
    @patch('homey_mcp.tools.resources.ensure_client')
    @patch('homey_mcp.tools.resources._resource_cache')
    async def test_flow_catalog_success(self, mock_cache, mock_ensure_client, mock_client_with_flows):
        """Test successful flow catalog resource generation."""
        mock_ensure_client.return_value = mock_client_with_flows
        
        # Mock cache to return fresh data
        expected_data = {
            "flows": [
                {
                    "id": "flow1",
                    "name": "Morning Routine",
                    "enabled": True,
                    "folder": None,
                    "type": "normal",
                    "trigger": {"id": "trigger1", "uri": "homey:manager:cron", "title": "Time Trigger"},
                    "conditions": [{"id": "condition1", "uri": "homey:manager:logic", "title": "Logic Condition"}],
                    "actions": [{"id": "action1", "uri": "homey:device:control", "title": "Device Action"}],
                    "broken": False,
                    "last_executed": "2024-01-01T08:00:00Z",
                    "statistics": {
                        "condition_count": 1,
                        "action_count": 1,
                        "has_trigger": True,
                        "is_broken": False
                    }
                },
                {
                    "id": "flow2",
                    "name": "Security Alert",
                    "enabled": False,
                    "folder": "security",
                    "type": "normal",
                    "trigger": {},
                    "conditions": [],
                    "actions": [],
                    "broken": True,
                    "last_executed": None,
                    "statistics": {
                        "condition_count": 0,
                        "action_count": 0,
                        "has_trigger": False,
                        "is_broken": True
                    }
                }
            ],
            "summary": {
                "total_count": 2,
                "enabled_count": 1,
                "disabled_count": 1,
                "flow_types": ["normal"],
                "trigger_types": ["homey"]
            }
        }
        mock_cache.get_or_fetch = AsyncMock(return_value=expected_data)
        
        result = await resources_module.flow_catalog_resource.fn()
        
        assert isinstance(result, dict)
        assert result == expected_data
        mock_cache.get_or_fetch.assert_called_once()
    
    @patch('homey_mcp.tools.resources.ensure_client')
    @patch('homey_mcp.tools.resources._resource_cache')
    async def test_flow_catalog_generic_error(self, mock_cache, mock_ensure_client):
        """Test flow catalog resource with generic error."""
        mock_ensure_client.return_value = AsyncMock()
        mock_cache.get_or_fetch.side_effect = ValueError("Some error")
        
        result = await resources_module.flow_catalog_resource.fn()
        
        assert isinstance(result, dict)
        assert "unexpected error" in result["error"]
        assert result["error_type"] == "unknown"


class TestResourceIntegration:
    """Integration tests for resource functionality."""
    
    @patch.dict('os.environ', {'HOMEY_API_URL': 'http://test.local', 'HOMEY_API_TOKEN': 'test_token'})
    @patch('homey_mcp.tools.resources._resource_cache')
    async def test_all_resources_handle_connection_errors(self, mock_cache):
        """Test that all resources handle connection errors gracefully."""
        mock_cache.get_or_fetch.side_effect = ConnectionError("Connection failed")
        
        resources = [
            resources_module.system_overview_resource.fn,
            resources_module.device_registry_resource.fn,
            resources_module.zone_hierarchy_resource.fn,
            resources_module.flow_catalog_resource.fn,
        ]
        
        for resource_func in resources:
            result = await resource_func()
            assert isinstance(result, dict)
            assert "error" in result
            assert result["error_type"] == "connection"
    
    @patch.dict('os.environ', {'HOMEY_API_URL': 'http://test.local', 'HOMEY_API_TOKEN': 'test_token'})
    @patch('homey_mcp.tools.resources._resource_cache')
    async def test_all_resources_handle_timeout_errors(self, mock_cache):
        """Test that all resources handle timeout errors gracefully."""
        mock_cache.get_or_fetch.side_effect = TimeoutError("Request timed out")
        
        resources = [
            resources_module.system_overview_resource.fn,
            resources_module.device_registry_resource.fn,
            resources_module.zone_hierarchy_resource.fn,
            resources_module.flow_catalog_resource.fn,
        ]
        
        for resource_func in resources:
            result = await resource_func()
            assert isinstance(result, dict)
            assert "error" in result
            assert result["error_type"] == "timeout"
    
    @patch('homey_mcp.tools.resources._resource_cache')
    async def test_all_resources_handle_generic_errors(self, mock_cache):
        """Test that all resources handle generic errors gracefully."""
        mock_cache.get_or_fetch.side_effect = ValueError("Some error")
        
        resources = [
            resources_module.system_overview_resource.fn,
            resources_module.device_registry_resource.fn,
            resources_module.zone_hierarchy_resource.fn,
            resources_module.flow_catalog_resource.fn,
        ]
        
        for resource_func in resources:
            result = await resource_func()
            assert isinstance(result, dict)
            assert "error" in result
            assert result["error_type"] == "unknown"
    
    @patch('homey_mcp.tools.resources._resource_cache')
    async def test_all_resources_return_dicts(self, mock_cache):
        """Test that all resources return dictionary data."""
        mock_cache.get_or_fetch = AsyncMock(return_value={"test": "data"})
        
        resources = [
            resources_module.system_overview_resource.fn,
            resources_module.device_registry_resource.fn,
            resources_module.zone_hierarchy_resource.fn,
            resources_module.flow_catalog_resource.fn,
        ]
        
        for resource_func in resources:
            result = await resource_func()
            assert isinstance(result, dict)
            assert len(result) > 0
    
    @patch.dict('os.environ', {'HOMEY_API_URL': 'http://test.local', 'HOMEY_API_TOKEN': 'test_token'})
    @patch('homey_mcp.tools.resources._resource_cache')
    async def test_all_resources_handle_stale_data(self, mock_cache):
        """Test that all resources handle stale data responses."""
        stale_response = {
            "data": {"test": "stale_data", "cache_info": {}},
            "is_stale": True,
            "error_type": "connection"
        }
        mock_cache.get_or_fetch = AsyncMock(return_value=stale_response)
        
        resources = [
            resources_module.system_overview_resource.fn,
            resources_module.device_registry_resource.fn,
            resources_module.zone_hierarchy_resource.fn,
            resources_module.flow_catalog_resource.fn,
        ]
        
        for resource_func in resources:
            result = await resource_func()
            assert isinstance(result, dict)
            assert len(result) > 0
            assert "cache_info" in result
            assert result["cache_info"]["is_stale"] is True