#!/usr/bin/env python3
"""
HomeyPro MCP Server

A Model Context Protocol (MCP) server for interacting with HomeyPro home automation systems.
Provides paginated access to devices, zones, and flows with comprehensive management capabilities.
"""

import asyncio
import os

from homey_mcp.client.manager import ensure_client, disconnect_client
from homey_mcp.utils.logging import get_logger
from homey_mcp.mcp_instance import mcp
from homey_mcp.tools import register_all_tools

# Register all tools at import time
register_all_tools()

logger = get_logger(__name__)


async def main():
    """Run the MCP server."""
    try:
        # Validate environment variables
        if not os.getenv("HOMEY_API_URL"):
            logger.error("HOMEY_API_URL environment variable is required")
            return

        if not os.getenv("HOMEY_API_TOKEN"):
            logger.error("HOMEY_API_TOKEN environment variable is required")
            return

        # Test connection
        await ensure_client()

        # Run the server
        await mcp.run()

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        # Cleanup
        await disconnect_client()


if __name__ == "__main__":
    asyncio.run(main())