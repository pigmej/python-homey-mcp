"""Client management for HomeyPro MCP Server."""

import os
from typing import Optional
from urllib.parse import urlparse

import homey

from ..config import get_config
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Global client instance
homey_client: Optional[homey.HomeyClient] = None


async def ensure_client() -> homey.HomeyClient:
    """Ensure we have a valid Homey client."""
    global homey_client

    if homey_client is None:
        config = get_config()

        try:
            homey_client = await homey.create_client(
                base_url=config.api_url,
                token=config.api_token,
                timeout=config.timeout,
                verify_ssl=config.verify_ssl,
            )
            logger.info(f"Connected to Homey at {config.api_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Homey: {e}")
            raise

    return homey_client


async def disconnect_client() -> None:
    """Disconnect the global client."""
    global homey_client
    if homey_client:
        try:
            await homey_client.disconnect()
            homey_client = None
        except Exception as e:
            logger.error(f"Error disconnecting client: {e}")
            raise