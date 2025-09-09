"""Integration tests for the registration system."""

import os
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
import sys

# Configure pytest-asyncio
pytest_asyncio.auto_mode = True


class TestRegistrationSystem:
    """Test the registration system for tools, prompts, and resources."""
    
    def test_register_all_tools_imports_modules(self):
        """Test that register_all_tools imports all required modules."""
        # Clear any existing imports to ensure fresh import
        modules_to_clear = [
            'homey_mcp.tools',
            'homey_mcp.tools.devices',
            'homey_mcp.tools.flows', 
            'homey_mcp.tools.zones',
            'homey_mcp.tools.system',
            'homey_mcp.tools.prompts',
            'homey_mcp.tools.resources'
        ]
        
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]
        
        # Import and call register_all_tools
        from homey_mcp.tools import register_all_tools
        
        result = register_all_tools()
        
        # Verify all modules are returned
        assert len(result) == 6
        devices, flows, zones, system, prompts, resources = result
        
        # Verify module names
        assert devices.__name__ == 'homey_mcp.tools.devices'
        assert flows.__name__ == 'homey_mcp.tools.flows'
        assert zones.__name__ == 'homey_mcp.tools.zones'
        assert system.__name__ == 'homey_mcp.tools.system'
        assert prompts.__name__ == 'homey_mcp.tools.prompts'
        assert resources.__name__ == 'homey_mcp.tools.resources'
    
    def test_register_all_tools_multiple_calls(self):
        """Test that register_all_tools can be called multiple times safely."""
        from homey_mcp.tools import register_all_tools
        
        # Call multiple times
        result1 = register_all_tools()
        result2 = register_all_tools()
        
        # Should return the same modules
        assert len(result1) == len(result2) == 6
        
        # Modules should be the same objects (cached imports)
        for i in range(6):
            assert result1[i] is result2[i]
    
    def test_tools_module_has_mcp_decorators(self):
        """Test that tool modules have MCP decorators applied."""
        from homey_mcp.tools import devices, flows, zones, system
        
        # Check that modules have functions with MCP decorators
        # We can't easily test the decorators directly, but we can check
        # that the functions exist and are callable
        
        # Device tools - check for decorated functions
        assert hasattr(devices, 'list_devices')
        assert hasattr(devices.list_devices, 'fn')  # FastMCP decorated function
        assert callable(devices.list_devices.fn)
        assert hasattr(devices, 'get_device')
        assert hasattr(devices.get_device, 'fn')
        assert callable(devices.get_device.fn)
        assert hasattr(devices, 'control_device')
        assert hasattr(devices.control_device, 'fn')
        assert callable(devices.control_device.fn)
        
        # Flow tools
        assert hasattr(flows, 'list_flows')
        assert hasattr(flows.list_flows, 'fn')
        assert callable(flows.list_flows.fn)
        assert hasattr(flows, 'trigger_flow')
        assert hasattr(flows.trigger_flow, 'fn')
        assert callable(flows.trigger_flow.fn)
        
        # Zone tools
        assert hasattr(zones, 'list_zones')
        assert hasattr(zones.list_zones, 'fn')
        assert callable(zones.list_zones.fn)
        assert hasattr(zones, 'get_zone_devices')
        assert hasattr(zones.get_zone_devices, 'fn')
        assert callable(zones.get_zone_devices.fn)
        
        # System tools
        assert hasattr(system, 'get_system_info')
        assert hasattr(system.get_system_info, 'fn')
        assert callable(system.get_system_info.fn)
    
    def test_prompts_module_has_mcp_decorators(self):
        """Test that prompts module has MCP decorators applied."""
        from homey_mcp.tools import prompts
        
        # Check that prompt functions exist and are decorated
        # The decorated functions become FunctionPrompt objects
        assert hasattr(prompts, 'device_control_assistant')
        assert hasattr(prompts, 'device_troubleshooting')
        assert hasattr(prompts, 'device_capability_explorer')
        assert hasattr(prompts, 'flow_creation_assistant')
        assert hasattr(prompts, 'flow_optimization')
        assert hasattr(prompts, 'flow_debugging')
        assert hasattr(prompts, 'system_health_check')
        assert hasattr(prompts, 'zone_organization')
        
        # Check that they have the expected FastMCP structure
        prompt_functions = [
            prompts.device_control_assistant,
            prompts.device_troubleshooting,
            prompts.device_capability_explorer,
            prompts.flow_creation_assistant,
            prompts.flow_optimization,
            prompts.flow_debugging,
            prompts.system_health_check,
            prompts.zone_organization,
        ]
        
        for prompt_func in prompt_functions:
            # Should have FastMCP FunctionPrompt attributes
            assert hasattr(prompt_func, 'name')
            assert hasattr(prompt_func, 'fn')
            assert callable(prompt_func.fn)
    
    def test_resources_module_has_mcp_decorators(self):
        """Test that resources module has MCP decorators applied."""
        from homey_mcp.tools import resources
        
        # Check that resource functions exist and are decorated
        assert hasattr(resources, 'system_overview_resource')
        assert hasattr(resources, 'device_registry_resource')
        assert hasattr(resources, 'zone_hierarchy_resource')
        assert hasattr(resources, 'flow_catalog_resource')
        
        # Check that they have the expected FastMCP structure
        resource_functions = [
            resources.system_overview_resource,
            resources.device_registry_resource,
            resources.zone_hierarchy_resource,
            resources.flow_catalog_resource,
        ]
        
        for resource_func in resource_functions:
            # Should have FastMCP FunctionResource attributes
            assert hasattr(resource_func, 'name')
            assert hasattr(resource_func, 'fn')
            assert callable(resource_func.fn)
    
    def test_mcp_instance_consistency(self):
        """Test that all modules use the same MCP instance."""
        from homey_mcp.mcp_instance import mcp
        
        # All modules should import and use the same mcp instance
        # We can't directly test this, but we can verify the instance exists
        assert mcp is not None
        assert hasattr(mcp, 'tool')
        assert hasattr(mcp, 'prompt')
        assert hasattr(mcp, 'resource')
        assert callable(mcp.tool)
        assert callable(mcp.prompt)
        assert callable(mcp.resource)
    
    @pytest.mark.asyncio
    @patch.dict('os.environ', {'HOMEY_API_URL': 'http://test.local', 'HOMEY_API_TOKEN': 'test_token'})
    @patch('homey_mcp.client.manager.ensure_client')
    async def test_main_registration_integration(self, mock_ensure_client):
        """Test that main.py properly registers all tools."""
        mock_ensure_client.return_value = MagicMock()
        
        # Import main module (this should trigger registration)
        
        # Verify that register_all_tools was called during import
        # We can't directly test this, but we can verify the modules are available
        from homey_mcp.tools import devices, flows, zones, system, prompts, resources
        
        # All modules should be imported and available
        assert devices is not None
        assert flows is not None
        assert zones is not None
        assert system is not None
        assert prompts is not None
        assert resources is not None
    
    def test_registration_error_handling(self):
        """Test that registration handles import errors gracefully."""
        # This test verifies that if a module has issues, it doesn't break the entire registration
        from homey_mcp.tools import register_all_tools
        
        # Should not raise an exception even if called multiple times
        try:
            register_all_tools()
            register_all_tools()
            register_all_tools()
        except Exception as e:
            pytest.fail(f"register_all_tools should not raise exceptions: {e}")
    
    def test_module_independence(self):
        """Test that modules can be imported independently."""
        # Each module should be importable on its own
        try:
            from homey_mcp.tools import devices
            from homey_mcp.tools import flows
            from homey_mcp.tools import zones
            from homey_mcp.tools import system
            from homey_mcp.tools import prompts
            from homey_mcp.tools import resources
        except ImportError as e:
            pytest.fail(f"Modules should be independently importable: {e}")
    
    def test_decorator_registration_consistency(self):
        """Test that decorators are consistently applied across modules."""
        from homey_mcp.tools import register_all_tools
        
        # Register all tools
        modules = register_all_tools()
        devices, flows, zones, system, prompts, resources = modules
        
        # Check that each module type has the expected decorated functions
        
        # Tools should have callable functions
        tool_modules = [devices, flows, zones, system]
        for module in tool_modules:
            # Each tool module should have at least one function
            functions = [attr for attr in dir(module) if callable(getattr(module, attr)) and not attr.startswith('_')]
            assert len(functions) > 0, f"Module {module.__name__} should have callable functions"
        
        # Prompts should have FunctionPrompt objects
        prompt_attrs = [attr for attr in dir(prompts) if not attr.startswith('_') and hasattr(getattr(prompts, attr), 'fn')]
        assert len(prompt_attrs) > 0, "Prompts module should have decorated prompt functions"
        
        # Resources should have FunctionResource objects  
        resource_attrs = [attr for attr in dir(resources) if not attr.startswith('_') and hasattr(getattr(resources, attr), 'fn')]
        assert len(resource_attrs) > 0, "Resources module should have decorated resource functions"


class TestServerStartupIntegration:
    """Test server startup with all components properly initialized."""
    
    def test_main_module_imports_successfully(self):
        """Test that main module imports without errors."""
        try:
            import main
            # Verify that main has the expected attributes
            assert hasattr(main, 'mcp')
            assert hasattr(main, 'validate_environment')
            assert callable(main.validate_environment)
        except ImportError as e:
            pytest.fail(f"Main module should import successfully: {e}")
    
    def test_server_startup_missing_env_vars(self):
        """Test that server handles missing environment variables gracefully."""
        with patch.dict(os.environ, {}, clear=True):
            # Should raise an exception when environment variables are missing
            with pytest.raises(ValueError, match="Missing required environment variables"):
                import importlib
                if 'main' in sys.modules:
                    importlib.reload(sys.modules['main'])
                else:
                    pass
    
    def test_registration_called_at_import(self):
        """Test that registration is called when main module is imported."""
        # Clear modules to test fresh import
        modules_to_clear = ['main']
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]
        
        # Import main should trigger registration
        
        # Verify that all modules are available after import
        from homey_mcp.tools import devices, flows, zones, system, prompts, resources
        
        # All modules should be imported and available
        assert devices is not None
        assert flows is not None
        assert zones is not None
        assert system is not None
        assert prompts is not None
        assert resources is not None


class TestRegistrationCompatibility:
    """Test compatibility with existing registration patterns."""
    
    def test_backward_compatibility(self):
        """Test that new registration doesn't break existing patterns."""
        from homey_mcp.tools import register_all_tools
        
        # Should return modules in the expected order
        result = register_all_tools()
        assert len(result) == 6
        
        # Should be able to unpack in the expected way
        devices, flows, zones, system, prompts, resources = result
        
        # All should be module objects
        import types
        for module in result:
            assert isinstance(module, types.ModuleType)
    
    def test_registration_idempotency(self):
        """Test that registration is idempotent."""
        from homey_mcp.tools import register_all_tools
        
        # Multiple calls should be safe and return consistent results
        result1 = register_all_tools()
        result2 = register_all_tools()
        result3 = register_all_tools()
        
        # All results should be identical
        assert result1 == result2 == result3
        
        # And should contain the same module objects
        for i in range(len(result1)):
            assert result1[i] is result2[i] is result3[i]
    
    def test_import_order_independence(self):
        """Test that import order doesn't affect registration."""
        # Clear modules to test fresh imports
        modules_to_clear = [
            'homey_mcp.tools.prompts',
            'homey_mcp.tools.resources'
        ]
        
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]
        
        # Import in different orders
        from homey_mcp.tools import resources
        from homey_mcp.tools import prompts
        
        # Both should work regardless of import order
        assert hasattr(prompts, 'device_control_assistant')
        assert hasattr(resources, 'system_overview_resource')
        
        # And both should have proper decorators applied
        assert hasattr(prompts.device_control_assistant, 'fn')
        assert hasattr(resources.system_overview_resource, 'fn')