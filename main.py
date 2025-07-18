#!/usr/bin/env python3
"""
HomeyPro MCP Server

A Model Context Protocol (MCP) server for interacting with HomeyPro home automation systems.
Provides paginated access to devices, zones, and flows with comprehensive management capabilities.
"""

import os
from homey_mcp.mcp_instance import mcp
from homey_mcp.tools import register_all_tools
from homey_mcp.utils.logging import get_logger

# Register all tools at import time
register_all_tools()

logger = get_logger(__name__)

# Validate environment variables at import time
def validate_environment():
    """Validate required environment variables."""
    required_vars = ["HOMEY_API_URL", "HOMEY_API_TOKEN"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

# Validate environment when module is imported
validate_environment()

# Export the mcp instance for FastMCP CLI
__all__ = ["mcp"]