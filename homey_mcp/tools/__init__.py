"""Tools module for HomeyPro MCP Server."""


def register_all_tools():
    """Register all MCP tools by importing the tool modules."""
    # Import all tool modules to trigger their @mcp.tool() decorators
    from . import devices, flows, zones, system
    
    # Return a tuple of the modules for reference if needed
    return devices, flows, zones, system