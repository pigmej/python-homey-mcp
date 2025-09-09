"""Unit tests for device functionality."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Configure pytest-asyncio
pytest_asyncio.auto_mode = True

import homey_mcp.tools.devices as devices_module
from homey_mcp.utils.pagination import PaginationError


class TestListDevices:
    """Test list_devices function."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock client with sample device data."""
        client = AsyncMock()
        
        # Mock devices
        mock_device1 = MagicMock()
        mock_device1.hidden = False
        mock_device1.is_online.return_value = True
        mock_device1.model_dump_compact.return_value = {
            "id": "device1",
            "name": "Living Room Light",
            "class_": "light"
        }
        mock_device1.model_dump.return_value = {
            "id": "device1",
            "name": "Living Room Light",
            "class_": "light",
            "capabilities": {"onoff": True, "dim": 0.8}
        }
        
        mock_device2 = MagicMock()
        mock_device2.hidden = False
        mock_device2.is_online.return_value = False
        mock_device2.model_dump_compact.return_value = {
            "id": "device2",
            "name": "Temperature Sensor",
            "class_": "sensor"
        }
        mock_device2.model_dump.return_value = {
            "id": "device2",
            "name": "Temperature Sensor",
            "class_": "sensor",
            "capabilities": {"measure_temperature": 22.5}
        }
        
        # Mock hidden device (should be filtered out)
        mock_device3 = MagicMock()
        mock_device3.hidden = True
        
        client.devices.get_devices.return_value = [mock_device1, mock_device2, mock_device3]
        
        return client
    
    @patch('homey_mcp.tools.devices.ensure_client')
    @patch('homey_mcp.tools.devices.parse_cursor')
    @patch('homey_mcp.tools.devices.paginate_results')
    async def test_list_devices_success_compact(self, mock_paginate, mock_parse_cursor, mock_ensure_client, mock_client):
        """Test successful device listing with compact format."""
        mock_ensure_client.return_value = mock_client
        mock_parse_cursor.return_value = {"offset": 0, "limit": 10}
        mock_paginate.return_value = {
            "items": [{"id": "device1", "name": "Living Room Light", "is_online": True}],
            "total_count": 2,
            "page_size": 10,
            "offset": 0,
            "has_next": False,
            "next_cursor": None
        }
        
        result = await devices_module.list_devices.fn()
        
        assert "devices" in result
        assert "pagination" in result
        assert result["pagination"]["total_count"] == 2
        mock_ensure_client.assert_called_once()
        mock_client.devices.get_devices.assert_called_once()
    
    @patch('homey_mcp.tools.devices.ensure_client')
    @patch('homey_mcp.tools.devices.parse_cursor')
    @patch('homey_mcp.tools.devices.paginate_results')
    async def test_list_devices_success_full(self, mock_paginate, mock_parse_cursor, mock_ensure_client, mock_client):
        """Test successful device listing with full format."""
        mock_ensure_client.return_value = mock_client
        mock_parse_cursor.return_value = {"offset": 0, "limit": 10}
        mock_paginate.return_value = {
            "items": [{"id": "device1", "name": "Living Room Light", "is_online": True}],
            "total_count": 2,
            "page_size": 10,
            "offset": 0,
            "has_next": False,
            "next_cursor": None
        }
        
        result = await devices_module.list_devices.fn(compact=False)
        
        assert "devices" in result
        assert "pagination" in result
        mock_ensure_client.assert_called_once()
    
    @patch('homey_mcp.tools.devices.ensure_client')
    @patch('homey_mcp.tools.devices.parse_cursor')
    async def test_list_devices_pagination_error(self, mock_parse_cursor, mock_ensure_client):
        """Test device listing with pagination error."""
        mock_ensure_client.return_value = AsyncMock()
        mock_parse_cursor.side_effect = PaginationError("Invalid cursor")
        
        result = await devices_module.list_devices.fn()
        
        assert "error" in result
        assert result["error_type"] == "pagination"
        assert "Invalid cursor" in result["error"]
        assert "suggested_action" in result
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_list_devices_connection_error(self, mock_ensure_client):
        """Test device listing with connection error."""
        mock_ensure_client.side_effect = ConnectionError("Connection failed")
        
        result = await devices_module.list_devices.fn()
        
        assert "error" in result
        assert result["error_type"] == "connection"
        assert "connection issues" in result["error"]
        assert "suggested_action" in result
        assert "details" in result
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_list_devices_timeout_error(self, mock_ensure_client):
        """Test device listing with timeout error."""
        mock_ensure_client.side_effect = TimeoutError("Request timed out")
        
        result = await devices_module.list_devices.fn()
        
        assert "error" in result
        assert result["error_type"] == "timeout"
        assert "timeout" in result["error"]
        assert "suggested_action" in result
        assert "details" in result
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_list_devices_generic_error(self, mock_ensure_client):
        """Test device listing with generic error."""
        mock_ensure_client.side_effect = ValueError("Some error")
        
        result = await devices_module.list_devices.fn()
        
        assert "error" in result
        assert result["error_type"] == "unknown"
        assert "unexpected error" in result["error"]
        assert "suggested_action" in result
        assert "details" in result


class TestGetDevice:
    """Test get_device function."""
    
    @pytest.fixture
    def mock_client_with_device(self):
        """Create a mock client with device data."""
        client = AsyncMock()
        
        # Mock device
        mock_device = MagicMock()
        mock_device.name = "Living Room Light"
        mock_device.is_online.return_value = True
        mock_device.model_dump_compact.return_value = {
            "id": "device1",
            "name": "Living Room Light",
            "class_": "light"
        }
        mock_device.model_dump.return_value = {
            "id": "device1",
            "name": "Living Room Light",
            "class_": "light",
            "capabilities": {"onoff": True, "dim": 0.8}
        }
        
        # Mock capabilities
        mock_capability = MagicMock()
        mock_capability.model_dump.return_value = {"type": "boolean", "getable": True, "setable": True}
        capabilities = {"onoff": mock_capability}
        
        # Mock settings
        settings = {"duration": 5}
        
        client.devices.get_device.return_value = mock_device
        client.devices.get_device_capabilities.return_value = capabilities
        client.devices.get_device_settings.return_value = settings
        
        return client
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_get_device_success(self, mock_ensure_client, mock_client_with_device):
        """Test successful device retrieval."""
        mock_ensure_client.return_value = mock_client_with_device
        
        result = await devices_module.get_device.fn("device1")
        
        assert "device" in result
        assert result["device"]["name"] == "Living Room Light"
        assert "is_online" in result["device"]
        assert "capabilities_detailed" in result["device"]
        assert "settings_detailed" in result["device"]
        mock_ensure_client.assert_called_once()
        mock_client_with_device.devices.get_device.assert_called_once_with("device1")
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_get_device_connection_error(self, mock_ensure_client):
        """Test device retrieval with connection error."""
        mock_ensure_client.side_effect = ConnectionError("Connection failed")
        
        result = await devices_module.get_device.fn("device1")
        
        assert "error" in result
        assert result["error_type"] == "connection"
        assert result["device_id"] == "device1"
        assert "connection issues" in result["error"]
        assert "suggested_action" in result
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_get_device_timeout_error(self, mock_ensure_client):
        """Test device retrieval with timeout error."""
        mock_ensure_client.side_effect = TimeoutError("Request timed out")
        
        result = await devices_module.get_device.fn("device1")
        
        assert "error" in result
        assert result["error_type"] == "timeout"
        assert result["device_id"] == "device1"
        assert "timeout" in result["error"]
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_get_device_generic_error(self, mock_ensure_client):
        """Test device retrieval with generic error."""
        mock_ensure_client.side_effect = ValueError("Some error")
        
        result = await devices_module.get_device.fn("device1")
        
        assert "error" in result
        assert result["error_type"] == "unknown"
        assert result["device_id"] == "device1"
        assert "unexpected error" in result["error"]


class TestGetDevicesClasses:
    """Test get_devices_classes function."""
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_get_devices_classes_success(self, mock_ensure_client):
        """Test successful device classes retrieval."""
        mock_client = AsyncMock()
        mock_client.devices.get_device_classes.return_value = ["light", "sensor", "thermostat"]
        mock_ensure_client.return_value = mock_client
        
        result = await devices_module.get_devices_classes.fn()
        
        assert "classes" in result
        assert result["classes"] == ["light", "sensor", "thermostat"]
        mock_ensure_client.assert_called_once()
        mock_client.devices.get_device_classes.assert_called_once()
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_get_devices_classes_connection_error(self, mock_ensure_client):
        """Test device classes retrieval with connection error."""
        mock_ensure_client.side_effect = ConnectionError("Connection failed")
        
        result = await devices_module.get_devices_classes.fn()
        
        assert "error" in result
        assert result["error_type"] == "connection"
        assert "connection issues" in result["error"]
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_get_devices_classes_timeout_error(self, mock_ensure_client):
        """Test device classes retrieval with timeout error."""
        mock_ensure_client.side_effect = TimeoutError("Request timed out")
        
        result = await devices_module.get_devices_classes.fn()
        
        assert "error" in result
        assert result["error_type"] == "timeout"
        assert "timeout" in result["error"]


class TestGetDevicesCapabilities:
    """Test get_devices_capabilities function."""
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_get_devices_capabilities_success(self, mock_ensure_client):
        """Test successful device capabilities retrieval."""
        mock_client = AsyncMock()
        mock_client.devices.get_devices_capabilities.return_value = ["onoff", "dim", "measure_temperature"]
        mock_ensure_client.return_value = mock_client
        
        result = await devices_module.get_devices_capabilities.fn()
        
        assert "capabilities" in result
        assert result["capabilities"] == ["onoff", "dim", "measure_temperature"]
        mock_ensure_client.assert_called_once()
        mock_client.devices.get_devices_capabilities.assert_called_once()
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_get_devices_capabilities_connection_error(self, mock_ensure_client):
        """Test device capabilities retrieval with connection error."""
        mock_ensure_client.side_effect = ConnectionError("Connection failed")
        
        result = await devices_module.get_devices_capabilities.fn()
        
        assert "error" in result
        assert result["error_type"] == "connection"
        assert "connection issues" in result["error"]


class TestSearchDevicesByName:
    """Test search_devices_by_name function."""
    
    @pytest.fixture
    def mock_client_with_search_results(self):
        """Create a mock client with search results."""
        client = AsyncMock()
        
        # Mock search results
        mock_device1 = MagicMock()
        mock_device1.hidden = False
        mock_device1.is_online.return_value = True
        mock_device1.model_dump_compact.return_value = {
            "id": "device1",
            "name": "Living Room Light",
            "class_": "light"
        }
        
        client.devices.search_devices_by_name.return_value = [mock_device1]
        
        return client
    
    @patch('homey_mcp.tools.devices.ensure_client')
    @patch('homey_mcp.tools.devices.parse_cursor')
    @patch('homey_mcp.tools.devices.paginate_results')
    async def test_search_devices_by_name_success(self, mock_paginate, mock_parse_cursor, mock_ensure_client, mock_client_with_search_results):
        """Test successful device search by name."""
        mock_ensure_client.return_value = mock_client_with_search_results
        mock_parse_cursor.return_value = {"offset": 0, "limit": 10}
        mock_paginate.return_value = {
            "items": [{"id": "device1", "name": "Living Room Light", "is_online": True}],
            "total_count": 1,
            "page_size": 10,
            "offset": 0,
            "has_next": False,
            "next_cursor": None
        }
        
        result = await devices_module.search_devices_by_name.fn("light")
        
        assert "devices" in result
        assert "query" in result
        assert result["query"] == "light"
        assert "pagination" in result
        mock_ensure_client.assert_called_once()
        mock_client_with_search_results.devices.search_devices_by_name.assert_called_once_with("light")
    
    @patch('homey_mcp.tools.devices.ensure_client')
    @patch('homey_mcp.tools.devices.parse_cursor')
    async def test_search_devices_by_name_pagination_error(self, mock_parse_cursor, mock_ensure_client):
        """Test device search with pagination error."""
        mock_ensure_client.return_value = AsyncMock()
        mock_parse_cursor.side_effect = PaginationError("Invalid cursor")
        
        result = await devices_module.search_devices_by_name.fn("light")
        
        assert "error" in result
        assert result["error_type"] == "pagination"
        assert result["query"] == "light"
        assert "Invalid cursor" in result["error"]
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_search_devices_by_name_connection_error(self, mock_ensure_client):
        """Test device search with connection error."""
        mock_ensure_client.side_effect = ConnectionError("Connection failed")
        
        result = await devices_module.search_devices_by_name.fn("light")
        
        assert "error" in result
        assert result["error_type"] == "connection"
        assert result["query"] == "light"
        assert "connection issues" in result["error"]


class TestSearchDevicesByClass:
    """Test search_devices_by_class function."""
    
    @patch('homey_mcp.tools.devices.ensure_client')
    @patch('homey_mcp.tools.devices.parse_cursor')
    @patch('homey_mcp.tools.devices.paginate_results')
    async def test_search_devices_by_class_success(self, mock_paginate, mock_parse_cursor, mock_ensure_client):
        """Test successful device search by class."""
        mock_client = AsyncMock()
        mock_device = MagicMock()
        mock_device.hidden = False
        mock_device.is_online.return_value = True
        mock_device.model_dump_compact.return_value = {"id": "device1", "name": "Light", "class_": "light"}
        
        mock_client.devices.search_devices_by_class.return_value = [mock_device]
        mock_ensure_client.return_value = mock_client
        mock_parse_cursor.return_value = {"offset": 0, "limit": 10}
        mock_paginate.return_value = {
            "items": [{"id": "device1", "name": "Light", "is_online": True}],
            "total_count": 1,
            "page_size": 10,
            "offset": 0,
            "has_next": False,
            "next_cursor": None
        }
        
        result = await devices_module.search_devices_by_class.fn("light")
        
        assert "devices" in result
        assert "query" in result
        assert result["query"] == "light"
        assert "pagination" in result
        mock_client.devices.search_devices_by_class.assert_called_once_with("light")
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_search_devices_by_class_timeout_error(self, mock_ensure_client):
        """Test device search by class with timeout error."""
        mock_ensure_client.side_effect = TimeoutError("Request timed out")
        
        result = await devices_module.search_devices_by_class.fn("light")
        
        assert "error" in result
        assert result["error_type"] == "timeout"
        assert result["query"] == "light"
        assert "timeout" in result["error"]


class TestControlDevice:
    """Test control_device function."""
    
    @pytest.fixture
    def mock_client_for_control(self):
        """Create a mock client for device control."""
        client = AsyncMock()
        
        # Mock successful control
        client.devices.set_capability_value.return_value = True
        
        # Mock device for getting current value
        mock_device = MagicMock()
        mock_device.name = "Living Room Light"
        mock_device.get_capability_value.return_value = True
        client.devices.get_device.return_value = mock_device
        
        return client
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_control_device_success(self, mock_ensure_client, mock_client_for_control):
        """Test successful device control."""
        mock_ensure_client.return_value = mock_client_for_control
        
        result = await devices_module.control_device.fn("device1", "onoff", True)
        
        assert result["success"] is True
        assert result["device_id"] == "device1"
        assert result["capability"] == "onoff"
        assert result["requested_value"] is True
        assert result["current_value"] is True
        assert result["device_name"] == "Living Room Light"
        mock_client_for_control.devices.set_capability_value.assert_called_once_with("device1", "onoff", True)
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_control_device_json_string_value(self, mock_ensure_client, mock_client_for_control):
        """Test device control with JSON string value."""
        mock_ensure_client.return_value = mock_client_for_control
        
        result = await devices_module.control_device.fn("device1", "onoff", "true")
        
        assert result["success"] is True
        # Should parse JSON string to boolean
        mock_client_for_control.devices.set_capability_value.assert_called_once_with("device1", "onoff", True)
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_control_device_invalid_json_string(self, mock_ensure_client, mock_client_for_control):
        """Test device control with invalid JSON string value."""
        mock_ensure_client.return_value = mock_client_for_control
        
        result = await devices_module.control_device.fn("device1", "onoff", "not_json")
        
        assert result["success"] is True
        # Should use string as-is when JSON parsing fails
        mock_client_for_control.devices.set_capability_value.assert_called_once_with("device1", "onoff", "not_json")
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_control_device_failure(self, mock_ensure_client):
        """Test device control failure."""
        mock_client = AsyncMock()
        mock_client.devices.set_capability_value.return_value = False
        mock_ensure_client.return_value = mock_client
        
        result = await devices_module.control_device.fn("device1", "onoff", True)
        
        assert result["success"] is False
        assert "error" in result
        assert result["device_id"] == "device1"
        assert result["capability"] == "onoff"
        assert result["requested_value"] is True
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_control_device_connection_error(self, mock_ensure_client):
        """Test device control with connection error."""
        mock_ensure_client.side_effect = ConnectionError("Connection failed")
        
        result = await devices_module.control_device.fn("device1", "onoff", True)
        
        assert "error" in result
        assert result["error_type"] == "connection"
        assert result["device_id"] == "device1"
        assert result["capability"] == "onoff"
        assert result["requested_value"] is True
        assert "connection issues" in result["error"]
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_control_device_timeout_error(self, mock_ensure_client):
        """Test device control with timeout error."""
        mock_ensure_client.side_effect = TimeoutError("Request timed out")
        
        result = await devices_module.control_device.fn("device1", "onoff", True)
        
        assert "error" in result
        assert result["error_type"] == "timeout"
        assert result["device_id"] == "device1"
        assert result["capability"] == "onoff"
        assert result["requested_value"] is True
        assert "timeout" in result["error"]


class TestGetDeviceInsights:
    """Test get_device_insights function."""
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_get_device_insights_success(self, mock_ensure_client):
        """Test successful device insights retrieval."""
        mock_client = AsyncMock()
        mock_insights = {"data": [{"timestamp": 1234567890, "value": 22.5}]}
        mock_client.devices.get_device_insights.return_value = mock_insights
        mock_ensure_client.return_value = mock_client
        
        result = await devices_module.get_device_insights.fn("device1", "measure_temperature", "last24Hours")
        
        assert "insights" in result
        assert result["device_id"] == "device1"
        assert result["insights"] == mock_insights
        mock_client.devices.get_device_insights.assert_called_once_with(
            "device1", "measure_temperature", "last24Hours", None, None
        )
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_get_device_insights_with_timestamps(self, mock_ensure_client):
        """Test device insights retrieval with timestamp parameters."""
        mock_client = AsyncMock()
        mock_insights = {"data": []}
        mock_client.devices.get_device_insights.return_value = mock_insights
        mock_ensure_client.return_value = mock_client
        
        result = await devices_module.get_device_insights.fn(
            "device1", "measure_temperature", "last24Hours", 1234567890, 1234567900
        )
        
        assert "insights" in result
        mock_client.devices.get_device_insights.assert_called_once_with(
            "device1", "measure_temperature", "last24Hours", 1234567890, 1234567900
        )
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_get_device_insights_pagination_error(self, mock_ensure_client):
        """Test device insights retrieval with pagination error."""
        mock_client = AsyncMock()
        mock_client.devices.get_device_insights.side_effect = PaginationError("Invalid parameters")
        mock_ensure_client.return_value = mock_client
        
        result = await devices_module.get_device_insights.fn("device1", "measure_temperature", "last24Hours")
        
        assert "error" in result
        assert result["error_type"] == "pagination"
        assert result["device_id"] == "device1"
        assert result["capability"] == "measure_temperature"
        assert "Invalid parameters" in result["error"]
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_get_device_insights_connection_error(self, mock_ensure_client):
        """Test device insights retrieval with connection error."""
        mock_ensure_client.side_effect = ConnectionError("Connection failed")
        
        result = await devices_module.get_device_insights.fn("device1", "measure_temperature", "last24Hours")
        
        assert "error" in result
        assert result["error_type"] == "connection"
        assert result["device_id"] == "device1"
        assert result["capability"] == "measure_temperature"
        assert "connection issues" in result["error"]
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_get_device_insights_timeout_error(self, mock_ensure_client):
        """Test device insights retrieval with timeout error."""
        mock_ensure_client.side_effect = TimeoutError("Request timed out")
        
        result = await devices_module.get_device_insights.fn("device1", "measure_temperature", "last24Hours")
        
        assert "error" in result
        assert result["error_type"] == "timeout"
        assert result["device_id"] == "device1"
        assert result["capability"] == "measure_temperature"
        assert "timeout" in result["error"]
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_get_device_insights_generic_error(self, mock_ensure_client):
        """Test device insights retrieval with generic error."""
        mock_ensure_client.side_effect = ValueError("Some error")
        
        result = await devices_module.get_device_insights.fn("device1", "measure_temperature", "last24Hours")
        
        assert "error" in result
        assert result["error_type"] == "unknown"
        assert result["device_id"] == "device1"
        assert result["capability"] == "measure_temperature"
        assert "unexpected error" in result["error"]


class TestDevicesIntegration:
    """Integration tests for device functionality."""
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_all_device_functions_handle_connection_errors(self, mock_ensure_client):
        """Test that all device functions handle connection errors gracefully."""
        mock_ensure_client.side_effect = ConnectionError("Connection failed")
        
        device_functions = [
            (devices_module.list_devices.fn, []),
            (devices_module.get_device.fn, ["device1"]),
            (devices_module.get_devices_classes.fn, []),
            (devices_module.get_devices_capabilities.fn, []),
            (devices_module.search_devices_by_name.fn, ["light"]),
            (devices_module.search_devices_by_class.fn, ["light"]),
            (devices_module.control_device.fn, ["device1", "onoff", True]),
            (devices_module.get_device_insights.fn, ["device1", "measure_temperature", "last24Hours"]),
        ]
        
        for func, args in device_functions:
            result = await func(*args)
            assert isinstance(result, dict)
            assert "error" in result
            assert result["error_type"] == "connection"
            assert "connection" in result["error"].lower()
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_all_device_functions_handle_timeout_errors(self, mock_ensure_client):
        """Test that all device functions handle timeout errors gracefully."""
        mock_ensure_client.side_effect = TimeoutError("Request timed out")
        
        device_functions = [
            (devices_module.list_devices.fn, []),
            (devices_module.get_device.fn, ["device1"]),
            (devices_module.get_devices_classes.fn, []),
            (devices_module.get_devices_capabilities.fn, []),
            (devices_module.search_devices_by_name.fn, ["light"]),
            (devices_module.search_devices_by_class.fn, ["light"]),
            (devices_module.control_device.fn, ["device1", "onoff", True]),
            (devices_module.get_device_insights.fn, ["device1", "measure_temperature", "last24Hours"]),
        ]
        
        for func, args in device_functions:
            result = await func(*args)
            assert isinstance(result, dict)
            assert "error" in result
            assert result["error_type"] == "timeout"
            assert "timeout" in result["error"].lower()
    
    @patch('homey_mcp.tools.devices.ensure_client')
    async def test_all_device_functions_handle_generic_errors(self, mock_ensure_client):
        """Test that all device functions handle generic errors gracefully."""
        mock_ensure_client.side_effect = ValueError("Some error")
        
        device_functions = [
            (devices_module.list_devices.fn, []),
            (devices_module.get_device.fn, ["device1"]),
            (devices_module.get_devices_classes.fn, []),
            (devices_module.get_devices_capabilities.fn, []),
            (devices_module.search_devices_by_name.fn, ["light"]),
            (devices_module.search_devices_by_class.fn, ["light"]),
            (devices_module.control_device.fn, ["device1", "onoff", True]),
            (devices_module.get_device_insights.fn, ["device1", "measure_temperature", "last24Hours"]),
        ]
        
        for func, args in device_functions:
            result = await func(*args)
            assert isinstance(result, dict)
            assert "error" in result
            assert result["error_type"] == "unknown"
            assert "error" in result["error"].lower()
    
    def test_all_device_functions_have_mcp_decorators(self):
        """Test that all device functions have MCP decorators applied."""
        device_functions = [
            devices_module.list_devices,
            devices_module.get_device,
            devices_module.get_devices_classes,
            devices_module.get_devices_capabilities,
            devices_module.search_devices_by_name,
            devices_module.search_devices_by_class,
            devices_module.control_device,
            devices_module.get_device_insights,
        ]
        
        for func in device_functions:
            # Should have FastMCP FunctionTool attributes
            assert hasattr(func, 'name')
            assert hasattr(func, 'fn')
            assert callable(func.fn)
    
    async def test_device_functions_return_consistent_structures(self):
        """Test that device functions return consistent data structures."""
        # This test verifies the structure without mocking to ensure consistency
        
        # Test error response structure consistency
        error_keys = ["error", "error_type", "suggested_action"]
        
        with patch('homey_mcp.tools.devices.ensure_client') as mock_ensure_client:
            mock_ensure_client.side_effect = ConnectionError("Connection failed")
            
            result = await devices_module.list_devices.fn()
            
            for key in error_keys:
                assert key in result, f"Missing key {key} in error response"
            
            assert result["error_type"] in ["connection", "timeout", "pagination", "unknown"]
            assert isinstance(result["suggested_action"], str)
            assert len(result["suggested_action"]) > 0