"""Simple tool configuration using FastMCP's native enable/disable functionality."""

import os
from ..utils.logging import get_logger

logger = get_logger(__name__)

# All available tool functions by module and name
TOOL_FUNCTIONS = {
    'devices': ['list_devices', 'get_device', 'get_devices_classes', 'get_devices_capabilities', 
                'search_devices_by_name', 'search_devices_by_class', 'control_device', 'get_device_insights'],
    'flows': ['list_flows', 'trigger_flow', 'get_flow_folders', 'get_flows_by_folder', 'get_flows_without_folder'],
    'zones': ['list_zones', 'get_zone_devices', 'get_zone_temp'],
    'system': ['get_system_info']
}


def configure_optional_tools():
    """Configure tools based on environment variables after all tools are registered."""
    
    # Get all available tools
    all_tool_names = []
    for tools in TOOL_FUNCTIONS.values():
        all_tool_names.extend(tools)
    
    # Check for explicit enabled tools list
    enabled_tools = os.getenv("HOMEY_ENABLED_TOOLS", "").strip()
    if enabled_tools:
        enabled_set = set(tool.strip() for tool in enabled_tools.split(",") if tool.strip())
        logger.info(f"Enabling only specific tools: {sorted(enabled_set)}")
        
        # Disable all tools not in the enabled list
        for tool_name in all_tool_names:
            if tool_name not in enabled_set:
                _disable_tool(tool_name)
        return
    
    # Check for disabled tools list
    disabled_tools = os.getenv("HOMEY_DISABLED_TOOLS", "").strip()
    if disabled_tools:
        disabled_set = set(tool.strip() for tool in disabled_tools.split(",") if tool.strip())
        logger.info(f"Disabling specific tools: {sorted(disabled_set)}")
        
        # Disable specified tools
        for tool_name in disabled_set:
            _disable_tool(tool_name)
        return
    
    # Default: all tools enabled (no action needed)
    logger.info("All tools enabled (default configuration)")


def _disable_tool(tool_name: str):
    """Disable a specific tool by name."""
    logger.debug(f"Disabling tool: {tool_name}")
    
    # Find the tool function and disable it
    for module_name, tool_names in TOOL_FUNCTIONS.items():
        if tool_name in tool_names:
            try:
                module = __import__(f'homey_mcp.tools.{module_name}', fromlist=[tool_name])
                if hasattr(module, tool_name):
                    tool_func = getattr(module, tool_name)
                    if hasattr(tool_func, 'disable'):
                        tool_func.disable()
                        return
            except (ImportError, AttributeError):
                continue
    
    logger.warning(f"Tool '{tool_name}' not found or cannot be disabled")