"""Client management for HomeyPro MCP Server."""

import os
from typing import Optional
from urllib.parse import urlparse

import homey

from ..utils.logging import get_logger

logger = get_logger(__name__)

# Global client instance
homey_client: Optional[homey.HomeyClient] = None


async def ensure_client() -> homey.HomeyClient:
    """Ensure we have a valid Homey client."""
    global homey_client

    if homey_client is None:
        base_url = os.getenv("HOMEY_API_URL")
        token = os.getenv("HOMEY_API_TOKEN")

        if not base_url or not token:
            raise ValueError(
                "HOMEY_API_URL and HOMEY_API_TOKEN environment variables are required"
            )

        # Validate URL format
        parsed = urlparse(base_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(
                "HOMEY_API_URL must be a valid URL (e.g., http://192.168.1.100)"
            )

        try:
            homey_client = await homey.create_client(
                base_url=base_url,
                token=token,
                timeout=30.0,
                verify_ssl=False,  # Often needed for local HomeyPro instances
            )
            logger.info(f"Connected to Homey at {base_url}")
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