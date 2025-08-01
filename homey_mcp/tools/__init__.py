"""Tools module for HomeyPro MCP Server."""


def register_all_tools():
    """Register all MCP tools, prompts, and resources by importing the modules."""
    # Import all tool modules to trigger their @mcp.tool() decorators
    from . import devices, flows, zones, system, health
    
    # Import prompt and resource modules to trigger their @mcp.prompt() and @mcp.resource() decorators
    from . import prompts, resources
    
    # Return a tuple of the modules for reference if needed
    return devices, flows, zones, system, health, prompts, resources
