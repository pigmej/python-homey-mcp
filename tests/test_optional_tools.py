"""Tests for optional tools functionality."""

import os
from unittest.mock import patch, MagicMock

from homey_mcp.utils.tool_config import configure_optional_tools, _disable_tool, TOOL_FUNCTIONS


class TestOptionalToolsConfiguration:
    """Test the optional tools configuration functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Clear any existing environment variables
        for var in ["HOMEY_ENABLED_TOOLS", "HOMEY_DISABLED_TOOLS"]:
            if var in os.environ:
                del os.environ[var]

    def teardown_method(self):
        """Clean up test environment."""
        # Clear any test environment variables
        for var in ["HOMEY_ENABLED_TOOLS", "HOMEY_DISABLED_TOOLS"]:
            if var in os.environ:
                del os.environ[var]

    def test_default_configuration_no_env_vars(self, caplog):
        """Test that all tools are enabled by default when no env vars are set."""
        with caplog.at_level('INFO', logger='homey_mcp.utils.tool_config'):
            configure_optional_tools()
            
            assert "All tools enabled (default configuration)" in caplog.text

    def test_disabled_tools_configuration(self, caplog):
        """Test disabling specific tools via HOMEY_DISABLED_TOOLS."""
        os.environ["HOMEY_DISABLED_TOOLS"] = "control_device,trigger_flow"
        
        with caplog.at_level('INFO', logger='homey_mcp.utils.tool_config'):
            with patch('homey_mcp.utils.tool_config._disable_tool') as mock_disable:
                configure_optional_tools()
                
                # Check that the right tools were marked for disabling
                assert "Disabling specific tools: ['control_device', 'trigger_flow']" in caplog.text
                
                # Verify disable was called for each tool
                assert mock_disable.call_count == 2
                mock_disable.assert_any_call('control_device')
                mock_disable.assert_any_call('trigger_flow')

    def test_enabled_tools_configuration(self, caplog):
        """Test enabling only specific tools via HOMEY_ENABLED_TOOLS."""
        os.environ["HOMEY_ENABLED_TOOLS"] = "get_system_info,list_zones"
        
        with caplog.at_level('INFO', logger='homey_mcp.utils.tool_config'):
            with patch('homey_mcp.utils.tool_config._disable_tool') as mock_disable:
                configure_optional_tools()
                
                # Check log message
                assert "Enabling only specific tools: ['get_system_info', 'list_zones']" in caplog.text
                
                # All tools except the enabled ones should be disabled
                # Total tools: 17, enabled: 2, so 15 should be disabled
                assert mock_disable.call_count == 15
                
                # Verify specific tools are NOT disabled
                disabled_calls = [call[0][0] for call in mock_disable.call_args_list]
                assert 'get_system_info' not in disabled_calls
                assert 'list_zones' not in disabled_calls
                
                # Verify some specific tools ARE disabled
                assert 'control_device' in disabled_calls
                assert 'trigger_flow' in disabled_calls

    def test_enabled_tools_takes_precedence_over_disabled(self, caplog):
        """Test that HOMEY_ENABLED_TOOLS takes precedence over HOMEY_DISABLED_TOOLS."""
        os.environ["HOMEY_ENABLED_TOOLS"] = "get_system_info"
        os.environ["HOMEY_DISABLED_TOOLS"] = "control_device"  # Should be ignored
        
        with caplog.at_level('INFO', logger='homey_mcp.utils.tool_config'):
            with patch('homey_mcp.utils.tool_config._disable_tool') as mock_disable:
                configure_optional_tools()
                
                # Should process enabled tools, not disabled
                assert "Enabling only specific tools: ['get_system_info']" in caplog.text
                assert "Disabling specific tools" not in caplog.text

    def test_empty_environment_variables(self, caplog):
        """Test handling of empty environment variables."""
        os.environ["HOMEY_ENABLED_TOOLS"] = ""
        os.environ["HOMEY_DISABLED_TOOLS"] = "  "  # Only whitespace
        
        with caplog.at_level('INFO', logger='homey_mcp.utils.tool_config'):
            configure_optional_tools()
            
            # Should fall back to default behavior
            assert "All tools enabled (default configuration)" in caplog.text

    def test_whitespace_handling_in_tool_lists(self, caplog):
        """Test that whitespace in tool lists is handled correctly."""
        os.environ["HOMEY_DISABLED_TOOLS"] = " control_device , trigger_flow , "
        
        with caplog.at_level('INFO', logger='homey_mcp.utils.tool_config'):
            with patch('homey_mcp.utils.tool_config._disable_tool') as mock_disable:
                configure_optional_tools()
                
                # Should still work despite extra whitespace
                assert mock_disable.call_count == 2
                mock_disable.assert_any_call('control_device')
                mock_disable.assert_any_call('trigger_flow')


class TestDisableToolFunction:
    """Test the _disable_tool function."""

    def test_disable_existing_tool(self, caplog):
        """Test disabling a tool that exists."""
        # Create a simple mock tool with disable method
        mock_tool = MagicMock()
        
        with caplog.at_level('DEBUG', logger='homey_mcp.utils.tool_config'):
            # Since we know the actual structure, let's test with existing modules
            # but mock just the specific tool function
            with patch('homey_mcp.tools.devices.control_device', mock_tool):
                _disable_tool('control_device')
                
                # Verify the tool's disable method was called
                mock_tool.disable.assert_called_once()
                assert "Disabling tool: control_device" in caplog.text

    def test_disable_nonexistent_tool(self, caplog):
        """Test disabling a tool that doesn't exist."""
        with caplog.at_level('DEBUG', logger='homey_mcp.utils.tool_config'):
            _disable_tool('nonexistent_tool')
            
            assert "Disabling tool: nonexistent_tool" in caplog.text
            assert "Tool 'nonexistent_tool' not found or cannot be disabled" in caplog.text

    def test_disable_tool_without_disable_method(self, caplog):
        """Test disabling a tool that exists but doesn't have disable method."""
        # Mock a tool function without disable method
        mock_tool = MagicMock(spec=[])
        
        with caplog.at_level('DEBUG', logger='homey_mcp.utils.tool_config'):
            with patch('builtins.__import__') as mock_import:
                mock_module = MagicMock()
                mock_module.get_system_info = mock_tool
                mock_import.return_value = mock_module
                
                _disable_tool('get_system_info')
                
                assert "Tool 'get_system_info' not found or cannot be disabled" in caplog.text

    def test_disable_tool_import_error(self, caplog):
        """Test handling of import errors when disabling tools."""
        with caplog.at_level('DEBUG', logger='homey_mcp.utils.tool_config'):
            with patch('builtins.__import__', side_effect=ImportError("Module not found")):
                _disable_tool('some_tool')
                
                assert "Tool 'some_tool' not found or cannot be disabled" in caplog.text


class TestToolFunctionsConstant:
    """Test the TOOL_FUNCTIONS constant."""

    def test_tool_functions_completeness(self):
        """Test that TOOL_FUNCTIONS contains all expected tools."""
        # Verify structure
        assert isinstance(TOOL_FUNCTIONS, dict)
        assert 'devices' in TOOL_FUNCTIONS
        assert 'flows' in TOOL_FUNCTIONS
        assert 'zones' in TOOL_FUNCTIONS
        assert 'system' in TOOL_FUNCTIONS

        # Verify device tools
        device_tools = TOOL_FUNCTIONS['devices']
        expected_device_tools = [
            'list_devices', 'get_device', 'get_devices_classes', 'get_devices_capabilities',
            'search_devices_by_name', 'search_devices_by_class', 'control_device', 'get_device_insights'
        ]
        assert set(device_tools) == set(expected_device_tools)

        # Verify flow tools
        flow_tools = TOOL_FUNCTIONS['flows']
        expected_flow_tools = [
            'list_flows', 'trigger_flow', 'get_flow_folders', 'get_flows_by_folder', 'get_flows_without_folder'
        ]
        assert set(flow_tools) == set(expected_flow_tools)

        # Verify zone tools
        zone_tools = TOOL_FUNCTIONS['zones']
        expected_zone_tools = ['list_zones', 'get_zone_devices', 'get_zone_temp']
        assert set(zone_tools) == set(expected_zone_tools)

        # Verify system tools
        system_tools = TOOL_FUNCTIONS['system']
        expected_system_tools = ['get_system_info']
        assert set(system_tools) == set(expected_system_tools)

    def test_total_tool_count(self):
        """Test that we have the expected total number of tools."""
        total_tools = sum(len(tools) for tools in TOOL_FUNCTIONS.values())
        assert total_tools == 17  # 8 + 5 + 3 + 1


class TestIntegrationWithToolRegistration:
    """Integration tests with actual tool registration."""

    def setup_method(self):
        """Set up test environment."""
        # Clear any existing environment variables
        for var in ["HOMEY_ENABLED_TOOLS", "HOMEY_DISABLED_TOOLS"]:
            if var in os.environ:
                del os.environ[var]

    def teardown_method(self):
        """Clean up test environment."""
        # Clear any test environment variables
        for var in ["HOMEY_ENABLED_TOOLS", "HOMEY_DISABLED_TOOLS"]:
            if var in os.environ:
                del os.environ[var]

    @patch.dict(os.environ, {"HOMEY_API_URL": "http://test", "HOMEY_API_TOKEN": "test"})
    def test_register_all_tools_with_disabled_tools(self, caplog):
        """Test that register_all_tools works with disabled tools configuration."""
        from homey_mcp.tools import register_all_tools
        
        os.environ["HOMEY_DISABLED_TOOLS"] = "control_device"
        
        with caplog.at_level('INFO'):
            # This should not raise any exceptions
            modules = register_all_tools()
            
            # Verify expected log messages
            assert "Registering all tool modules" in caplog.text
            assert "Disabling specific tools: ['control_device']" in caplog.text
            
            # Verify modules were returned
            assert len(modules) == 6  # devices, flows, zones, system, prompts, resources

    @patch.dict(os.environ, {"HOMEY_API_URL": "http://test", "HOMEY_API_TOKEN": "test"})
    def test_register_all_tools_with_enabled_tools_only(self, caplog):
        """Test that register_all_tools works with enabled tools configuration."""
        from homey_mcp.tools import register_all_tools
        
        os.environ["HOMEY_ENABLED_TOOLS"] = "get_system_info,list_zones"
        
        with caplog.at_level('INFO'):
            # This should not raise any exceptions
            modules = register_all_tools()
            
            # Verify expected log messages
            assert "Registering all tool modules" in caplog.text
            assert "Enabling only specific tools: ['get_system_info', 'list_zones']" in caplog.text
            
            # Verify modules were returned
            assert len(modules) == 6

    @patch.dict(os.environ, {"HOMEY_API_URL": "http://test", "HOMEY_API_TOKEN": "test"})
    def test_register_all_tools_default_configuration(self, caplog):
        """Test that register_all_tools works with default configuration."""
        from homey_mcp.tools import register_all_tools
        
        with caplog.at_level('INFO'):
            # This should not raise any exceptions
            modules = register_all_tools()
            
            # Verify expected log messages
            assert "Registering all tool modules" in caplog.text
            assert "All tools enabled (default configuration)" in caplog.text
            
            # Verify modules were returned
            assert len(modules) == 6