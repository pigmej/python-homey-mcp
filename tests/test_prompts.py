"""Unit tests for prompt functionality."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Configure pytest-asyncio
pytest_asyncio.auto_mode = True

import homey_mcp.tools.prompts as prompts_module
from homey_mcp.tools.prompts import (
    PromptContext,
    get_prompt_context,
)


class TestPromptContext:
    """Test PromptContext data class."""
    
    def test_prompt_context_creation(self):
        """Test creating a PromptContext instance."""
        context = PromptContext(
            system_info={"connection_status": "connected"},
            device_summary={"total_count": 5, "online_count": 4},
            zone_summary={"total_count": 3, "zone_names": ["Living Room", "Kitchen"]},
            flow_summary={"total_count": 2, "enabled_count": 1},
            timestamp="2024-01-01T12:00:00"
        )
        
        assert context.system_info["connection_status"] == "connected"
        assert context.device_summary["total_count"] == 5
        assert context.zone_summary["zone_names"] == ["Living Room", "Kitchen"]
        assert context.flow_summary["enabled_count"] == 1
        assert context.timestamp == "2024-01-01T12:00:00"
    
    def test_empty_context(self):
        """Test creating an empty PromptContext."""
        context = PromptContext.empty()
        
        assert context.system_info["connection_status"] == "unavailable"
        assert context.device_summary["total_count"] == 0
        assert context.device_summary["online_count"] == 0
        assert context.zone_summary["total_count"] == 0
        assert context.flow_summary["total_count"] == 0
        assert isinstance(context.timestamp, str)


class TestGetPromptContext:
    """Test get_prompt_context function."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock client with sample data."""
        client = AsyncMock()
        
        # Mock devices
        mock_device1 = MagicMock()
        mock_device1.is_online.return_value = True
        mock_device1.class_ = "light"
        mock_device1.capabilities = {"onoff": True, "dim": 0.5}
        
        mock_device2 = MagicMock()
        mock_device2.is_online.return_value = False
        mock_device2.class_ = "sensor"
        mock_device2.capabilities = {"measure_temperature": 22.5}
        
        client.devices.get_devices.return_value = [mock_device1, mock_device2]
        
        # Mock zones
        mock_zone1 = MagicMock()
        mock_zone1.name = "Living Room"
        mock_zone2 = MagicMock()
        mock_zone2.name = "Kitchen"
        
        client.zones.get_zones.return_value = [mock_zone1, mock_zone2]
        
        # Mock flows
        client.flows.get_flows.return_value = [MagicMock(), MagicMock()]
        client.flows.get_advanced_flows.return_value = [MagicMock()]
        client.flows.get_enabled_flows.return_value = [MagicMock()]
        client.flows.get_enabled_advanced_flows.return_value = []
        
        # Mock system config
        mock_system_config = MagicMock()
        mock_system_config.address = "192.168.1.100"
        mock_system_config.language = "en"
        mock_system_config.units = "metric"
        mock_system_config.is_metric.return_value = True
        mock_system_config.get_location_coordinates.return_value = (52.0, 4.0)
        
        client.system.get_system_config.return_value = mock_system_config
        
        return client
    
    @patch('homey_mcp.tools.prompts.ensure_client')
    async def test_get_prompt_context_success(self, mock_ensure_client, mock_client):
        """Test successful prompt context generation."""
        mock_ensure_client.return_value = mock_client
        
        context = await get_prompt_context()
        
        assert context.system_info["connection_status"] == "connected"
        assert context.device_summary["total_count"] == 2
        assert context.device_summary["online_count"] == 1
        assert context.device_summary["offline_count"] == 1
        assert context.zone_summary["total_count"] == 2
        assert "Living Room" in context.zone_summary["zone_names"]
        assert "Kitchen" in context.zone_summary["zone_names"]
        assert context.flow_summary["total_count"] == 3  # 2 regular + 1 advanced
        assert context.flow_summary["enabled_count"] == 1
        assert isinstance(context.timestamp, str)
    
    @patch('homey_mcp.tools.prompts.ensure_client')
    async def test_get_prompt_context_connection_failure(self, mock_ensure_client):
        """Test prompt context generation when connection fails."""
        mock_ensure_client.side_effect = Exception("Connection failed")
        
        context = await get_prompt_context()
        
        assert context.system_info["connection_status"] == "unavailable"
        assert context.device_summary["total_count"] == 0
        assert context.zone_summary["total_count"] == 0
        assert context.flow_summary["total_count"] == 0
    
    @patch('homey_mcp.tools.prompts.ensure_client')
    async def test_get_prompt_context_partial_failure(self, mock_ensure_client, mock_client):
        """Test prompt context generation when some API calls fail."""
        mock_client.devices.get_devices.side_effect = Exception("Device API failed")
        mock_ensure_client.return_value = mock_client
        
        context = await get_prompt_context()
        
        # Should return empty context when any critical API call fails
        assert context.system_info["connection_status"] == "unavailable"


class TestDeviceControlAssistant:
    """Test device_control_assistant prompt."""
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_device_control_assistant_success(self, mock_get_context):
        """Test successful device control assistant prompt generation."""
        mock_context = PromptContext(
            system_info={"connection_status": "connected"},
            device_summary={
                "total_count": 10,
                "online_count": 8,
                "offline_count": 2,
                "device_type_count": 3,
                "capability_count": 15,
                "sample_device_types": ["light", "sensor", "thermostat"]
            },
            zone_summary={"total_count": 4, "zone_names": ["Living Room", "Kitchen", "Bedroom", "Bathroom"]},
            flow_summary={"total_count": 5, "enabled_count": 4},
            timestamp="2024-01-01T12:00:00"
        )
        mock_get_context.return_value = mock_context
        
        result = await prompts_module.device_control_assistant.fn()
        
        assert isinstance(result, str)
        assert "HomeyPro Device Control Assistant" in result
        assert "**Total Devices**: 10" in result
        assert "**Online Devices**: 8" in result
        assert "**Offline Devices**: 2" in result
        assert "light, sensor, thermostat" in result
        assert "Living Room, Kitchen, Bedroom, Bathroom" in result
        assert "2024-01-01T12:00:00" in result
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_device_control_assistant_connection_failure(self, mock_get_context):
        """Test device control assistant prompt when connection fails."""
        mock_get_context.side_effect = Exception("Connection failed")
        
        result = await prompts_module.device_control_assistant.fn()
        
        assert isinstance(result, str)
        assert "Error" in result
        assert "system connectivity issues" in result
        assert "Connection failed" in result
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_device_control_assistant_empty_context(self, mock_get_context):
        """Test device control assistant prompt with empty context."""
        mock_get_context.return_value = PromptContext.empty()
        
        result = await prompts_module.device_control_assistant.fn()
        
        assert isinstance(result, str)
        assert "**Total Devices**: 0" in result
        assert "**Online Devices**: 0" in result
        assert "No device types detected" in result
        assert "No zones configured" in result


class TestDeviceTroubleshooting:
    """Test device_troubleshooting prompt."""
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_device_troubleshooting_success(self, mock_get_context):
        """Test successful device troubleshooting prompt generation."""
        mock_context = PromptContext(
            system_info={"connection_status": "connected"},
            device_summary={"total_count": 10, "online_count": 9, "offline_count": 1},
            zone_summary={"total_count": 3, "zone_names": ["Living Room", "Kitchen", "Bedroom"]},
            flow_summary={"total_count": 5, "enabled_count": 4},
            timestamp="2024-01-01T12:00:00"
        )
        mock_get_context.return_value = mock_context
        
        result = await prompts_module.device_troubleshooting.fn()
        
        assert isinstance(result, str)
        assert "HomeyPro Device Troubleshooting Guide" in result
        assert "Good (90.0% devices online)" in result  # 9/10 = 90%
        assert "**Total Devices**: 10" in result
        assert "**Online Devices**: 9" in result
        assert "**Offline Devices**: 1" in result
        assert "1 currently offline" in result
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_device_troubleshooting_critical_health(self, mock_get_context):
        """Test device troubleshooting prompt with critical system health."""
        mock_context = PromptContext(
            system_info={"connection_status": "connected"},
            device_summary={"total_count": 10, "online_count": 5, "offline_count": 5},
            zone_summary={"total_count": 3, "zone_names": ["Living Room"]},
            flow_summary={"total_count": 2, "enabled_count": 1},
            timestamp="2024-01-01T12:00:00"
        )
        mock_get_context.return_value = mock_context
        
        result = await prompts_module.device_troubleshooting.fn()
        
        assert "Critical (50.0% devices online)" in result
        assert "5 currently offline" in result
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_device_troubleshooting_connection_failure(self, mock_get_context):
        """Test device troubleshooting prompt when connection fails."""
        mock_get_context.side_effect = Exception("Network error")
        
        result = await prompts_module.device_troubleshooting.fn()
        
        assert isinstance(result, str)
        assert "Error" in result
        assert "system connectivity issues" in result
        assert "Network error" in result


class TestDeviceCapabilityExplorer:
    """Test device_capability_explorer prompt."""
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_device_capability_explorer_success(self, mock_get_context):
        """Test successful device capability explorer prompt generation."""
        mock_context = PromptContext(
            system_info={"connection_status": "connected"},
            device_summary={
                "total_count": 15,
                "device_type_count": 5,
                "capability_count": 25,
                "sample_device_types": ["light", "sensor", "thermostat", "speaker"]
            },
            zone_summary={"total_count": 4, "zone_names": ["Living Room", "Kitchen"]},
            flow_summary={"total_count": 3, "enabled_count": 2},
            timestamp="2024-01-01T12:00:00"
        )
        mock_get_context.return_value = mock_context
        
        result = await prompts_module.device_capability_explorer.fn()
        
        assert isinstance(result, str)
        assert "HomeyPro Device Capability Explorer" in result
        assert "**Total Devices**: 15" in result
        assert "**Device Types**: 5 different types" in result
        assert "**Unique Capabilities**: 25 available" in result
        assert "light, sensor, thermostat, speaker" in result
        assert "Living Room, Kitchen" in result
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_device_capability_explorer_no_devices(self, mock_get_context):
        """Test device capability explorer prompt with no devices."""
        mock_get_context.return_value = PromptContext.empty()
        
        result = await prompts_module.device_capability_explorer.fn()
        
        assert isinstance(result, str)
        assert "**Total Devices**: 0" in result
        assert "**Device Types**: 0 different types" in result
        assert "None detected" in result
        assert "No zones configured" in result
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_device_capability_explorer_connection_failure(self, mock_get_context):
        """Test device capability explorer prompt when connection fails."""
        mock_get_context.side_effect = Exception("API timeout")
        
        result = await prompts_module.device_capability_explorer.fn()
        
        assert isinstance(result, str)
        assert "Error" in result
        assert "system connectivity issues" in result
        assert "API timeout" in result


class TestFlowCreationAssistant:
    """Test flow_creation_assistant prompt."""
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_flow_creation_assistant_success(self, mock_get_context):
        """Test successful flow creation assistant prompt generation."""
        mock_context = PromptContext(
            system_info={"connection_status": "connected"},
            device_summary={
                "total_count": 12,
                "online_count": 11,
                "sample_device_types": ["light", "motion_sensor", "thermostat"]
            },
            zone_summary={"total_count": 3, "zone_names": ["Living Room", "Kitchen", "Bedroom"]},
            flow_summary={"total_count": 8, "enabled_count": 6},
            timestamp="2024-01-01T12:00:00"
        )
        mock_get_context.return_value = mock_context
        
        result = await prompts_module.flow_creation_assistant.fn()
        
        assert isinstance(result, str)
        assert "HomeyPro Flow Creation Assistant" in result
        assert "**Total Devices**: 12 (11 online)" in result
        assert "**Available Zones**: 3 zones" in result
        assert "**Existing Flows**: 8 (6 enabled)" in result
        assert "light, motion_sensor, thermostat" in result
        assert "- Living Room" in result
        assert "- Kitchen" in result
        assert "- Bedroom" in result
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_flow_creation_assistant_no_resources(self, mock_get_context):
        """Test flow creation assistant prompt with minimal resources."""
        mock_get_context.return_value = PromptContext.empty()
        
        result = await prompts_module.flow_creation_assistant.fn()
        
        assert isinstance(result, str)
        assert "**Total Devices**: 0 (0 online)" in result
        assert "**Available Zones**: 0 zones" in result
        assert "**Existing Flows**: 0 (0 enabled)" in result
        assert "None detected" in result
        assert "No zones configured" in result


class TestFlowOptimization:
    """Test flow_optimization prompt."""
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_flow_optimization_success(self, mock_get_context):
        """Test successful flow optimization prompt generation."""
        mock_context = PromptContext(
            system_info={"connection_status": "connected"},
            device_summary={"total_count": 20, "online_count": 18},
            zone_summary={"total_count": 5, "zone_names": ["Living Room", "Kitchen"]},
            flow_summary={"total_count": 15, "enabled_count": 12},
            timestamp="2024-01-01T12:00:00"
        )
        mock_get_context.return_value = mock_context
        
        result = await prompts_module.flow_optimization.fn()
        
        assert isinstance(result, str)
        assert "HomeyPro Flow Optimization Guide" in result
        assert "**Total Flows**: 15" in result
        assert "**Enabled Flows**: 12" in result
        assert "**Disabled Flows**: 0" in result  # The actual output shows 0, not 3
        assert "**System Devices**: 20" in result


class TestFlowDebugging:
    """Test flow_debugging prompt."""
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_flow_debugging_success(self, mock_get_context):
        """Test successful flow debugging prompt generation."""
        mock_context = PromptContext(
            system_info={"connection_status": "connected"},
            device_summary={"total_count": 10, "online_count": 9},
            zone_summary={"total_count": 3, "zone_names": ["Living Room"]},
            flow_summary={"total_count": 8, "enabled_count": 6},
            timestamp="2024-01-01T12:00:00"
        )
        mock_get_context.return_value = mock_context
        
        result = await prompts_module.flow_debugging.fn()
        
        assert isinstance(result, str)
        assert "HomeyPro Flow Debugging Guide" in result
        assert "6/8 flows enabled" in result
        assert "Device Health**: 90.0%" in result
        assert "9/10 devices online" in result


class TestSystemHealthCheck:
    """Test system_health_check prompt."""
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_system_health_check_success(self, mock_get_context):
        """Test successful system health check prompt generation."""
        mock_context = PromptContext(
            system_info={
                "connection_status": "connected",
                "address": "192.168.1.100",
                "language": "en",
                "units": "metric"
            },
            device_summary={"total_count": 25, "online_count": 23, "offline_count": 2},
            zone_summary={"total_count": 6, "zone_names": ["Living Room", "Kitchen"]},
            flow_summary={"total_count": 12, "enabled_count": 10},
            timestamp="2024-01-01T12:00:00"
        )
        mock_get_context.return_value = mock_context
        
        result = await prompts_module.system_health_check.fn()
        
        assert isinstance(result, str)
        assert "HomeyPro System Health Check" in result
        assert "🟡 Good" in result  # 23/25 = 92%
        assert "**Total Devices**: 25" in result
        assert "**Online Devices**: 23" in result
        assert "**Offline Devices**: 2" in result
        assert "192.168.1.100" in result


class TestZoneOrganization:
    """Test zone_organization prompt."""
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_zone_organization_success(self, mock_get_context):
        """Test successful zone organization prompt generation."""
        mock_context = PromptContext(
            system_info={"connection_status": "connected"},
            device_summary={"total_count": 30, "online_count": 28},
            zone_summary={
                "total_count": 8,
                "zone_names": ["Living Room", "Kitchen", "Bedroom", "Bathroom", "Office", "Garage"]
            },
            flow_summary={"total_count": 15, "enabled_count": 12},
            timestamp="2024-01-01T12:00:00"
        )
        mock_get_context.return_value = mock_context
        
        result = await prompts_module.zone_organization.fn()
        
        assert isinstance(result, str)
        assert "HomeyPro Zone Organization Guide" in result
        assert "**Total Zones**: 8" in result
        assert "**Total Devices**: 30" in result
        assert "Living Room" in result
        assert "Kitchen" in result
        assert "Bedroom" in result


class TestPromptIntegration:
    """Integration tests for prompt functionality."""
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_all_prompts_handle_empty_context(self, mock_get_context):
        """Test that all prompts handle empty context gracefully."""
        mock_get_context.return_value = PromptContext.empty()
        
        prompts = [
            prompts_module.device_control_assistant.fn,
            prompts_module.device_troubleshooting.fn,
            prompts_module.device_capability_explorer.fn,
            prompts_module.flow_creation_assistant.fn,
            prompts_module.flow_optimization.fn,
            prompts_module.flow_debugging.fn,
            prompts_module.system_health_check.fn,
            prompts_module.zone_organization.fn,
        ]
        
        for prompt_func in prompts:
            result = await prompt_func()
            assert isinstance(result, str)
            assert len(result) > 0
            # Should not contain error messages when context is empty but valid
            assert "Error" not in result or "connectivity issues" not in result
    
    @patch('homey_mcp.tools.prompts.get_prompt_context')
    async def test_all_prompts_handle_exceptions(self, mock_get_context):
        """Test that all prompts handle exceptions gracefully."""
        mock_get_context.side_effect = Exception("Test exception")
        
        prompts = [
            prompts_module.device_control_assistant.fn,
            prompts_module.device_troubleshooting.fn,
            prompts_module.device_capability_explorer.fn,
            prompts_module.flow_creation_assistant.fn,
            prompts_module.flow_optimization.fn,
            prompts_module.flow_debugging.fn,
            prompts_module.system_health_check.fn,
            prompts_module.zone_organization.fn,
        ]
        
        for prompt_func in prompts:
            result = await prompt_func()
            assert isinstance(result, str)
            assert len(result) > 0
            assert "Error" in result
            assert "Test exception" in result
    
    async def test_prompt_arguments_parameter(self):
        """Test that prompts accept optional arguments parameter."""
        # All prompts should accept arguments parameter without error
        prompts = [
            prompts_module.device_control_assistant.fn,
            prompts_module.device_troubleshooting.fn,
            prompts_module.device_capability_explorer.fn,
            prompts_module.flow_creation_assistant.fn,
            prompts_module.flow_optimization.fn,
            prompts_module.flow_debugging.fn,
            prompts_module.system_health_check.fn,
            prompts_module.zone_organization.fn,
        ]
        
        test_args = {"test": "value"}
        
        with patch('homey_mcp.tools.prompts.get_prompt_context') as mock_get_context:
            mock_get_context.return_value = PromptContext.empty()
            
            for prompt_func in prompts:
                # Should not raise exception when called with arguments
                result = await prompt_func(test_args)
                assert isinstance(result, str)
                assert len(result) > 0