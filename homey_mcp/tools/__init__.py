"""Tools module for HomeyPro MCP Server."""

from ..utils.logging import get_logger

logger = get_logger(__name__)


def register_all_tools():
    """Register all MCP tools, prompts, and resources by importing the modules."""
    imported_modules = []
    
    logger.info("Registering all tool modules")
    
    # Import all tool modules to register their @mcp.tool() decorators
    from . import devices, flows, zones, system
    imported_modules.extend([devices, flows, zones, system])
    logger.debug("Imported device, flow, zone, and system tools")
    
    # Always import prompt and resource modules
    from . import prompts, resources
    imported_modules.extend([prompts, resources])
    logger.debug("Imported prompts and resources")
    
    # Configure optional tools based on environment variables
    from ..utils.tool_config import configure_optional_tools
    configure_optional_tools()
    
    # Return tuple of imported modules for reference if needed
    return tuple(imported_modules)
