#!/usr/bin/env python3
"""
HomeyPro MCP Server

A Model Context Protocol (MCP) server for interacting with HomeyPro home automation systems.
Provides paginated access to devices, zones, and flows with comprehensive management capabilities.
"""

import asyncio
import json
import logging
import os
from operator import attrgetter
from typing import Any, Dict, List, Optional, Union
from pydantic.fields import Field
from typing_extensions import Annotated, Literal
from urllib.parse import urlparse

import homey
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default pagination settings
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100

# MCP server instance
mcp = FastMCP("HomeyPro")

# Global client instance
homey_client: Optional[homey.HomeyClient] = None


class PaginationError(Exception):
    """Raised when pagination parameters are invalid."""

    pass


def parse_cursor(cursor: Optional[str]) -> Dict[str, Any]:
    """Parse cursor string into pagination parameters."""
    if not cursor or cursor == "null":
        return {"offset": 0, "page_size": DEFAULT_PAGE_SIZE}

    try:
        data = json.loads(cursor)
        if not isinstance(data, dict):
            raise ValueError("Cursor must be a JSON object")

        offset = data.get("offset", 0)
        page_size = data.get("page_size", DEFAULT_PAGE_SIZE)

        if not isinstance(offset, int) or offset < 0:
            raise ValueError("Offset must be a non-negative integer")
        if (
            not isinstance(page_size, int)
            or page_size <= 0
            or page_size > MAX_PAGE_SIZE
        ):
            raise ValueError(f"Page size must be between 1 and {MAX_PAGE_SIZE}")

        return {"offset": offset, "page_size": page_size, **data}
    except (json.JSONDecodeError, ValueError) as e:
        raise PaginationError(f"Invalid cursor format: {e}")


def create_cursor(offset: int, page_size: int, **kwargs) -> str:
    """Create cursor string from pagination parameters."""
    data = {"offset": offset, "page_size": page_size, **kwargs}
    return json.dumps(data)


def paginate_results(items: List[Any], cursor_params: Dict[str, Any]) -> Dict[str, Any]:
    """Apply pagination to a list of items."""
    offset = cursor_params["offset"]
    page_size = cursor_params["page_size"]

    total_count = len(items)
    page_items = items[offset : offset + page_size]

    has_next = offset + page_size < total_count
    next_cursor = None
    if has_next:
        next_cursor = create_cursor(offset + page_size, page_size)

    return {
        "items": page_items,
        "total_count": total_count,
        "page_size": page_size,
        "offset": offset,
        "has_next": has_next,
        "next_cursor": next_cursor,
    }


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


@mcp.tool()
async def list_devices(
    cursor: Optional[str] = None,
    compact: Annotated[
        bool,
        Field(
            description="Optional switch for compact results, by default true. Switch only if really needed"
        ),
    ] = True,
) -> Dict[str, Any]:
    """
    List all devices with pagination support.

    Args:
        cursor: Optional cursor for pagination. If not provided, starts from the beginning.
        compact: Optional switch for compact results, by default true. Switch only if really needed

    Returns:
        Paginated list of devices with metadata.
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()
        if compact:
            dumper = attrgetter("model_dump_compact")
        else:
            dumper = attrgetter("model_dump")

        # Get all devices
        devices = await client.devices.get_devices()

        # Convert to dictionaries for serialization
        device_dicts = []
        for device in devices:
            device_dict = dumper(device)()
            # Add computed fields
            device_dict["is_online"] = device.is_online()
            device_dict["driver_id"] = device.get_driver_id()
            device_dict["zone_id"] = device.get_zone_id()
            device_dicts.append(device_dict)

        # Apply pagination
        result = paginate_results(device_dicts, cursor_params)

        return {
            "devices": result["items"],
            "pagination": {
                "total_count": result["total_count"],
                "page_size": result["page_size"],
                "offset": result["offset"],
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
            },
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        return {"error": f"Failed to list devices: {e}"}


@mcp.tool()
async def get_device(
    device_id: str,
    compact: Annotated[
        bool,
        Field(
            description="Optional switch for compact results, by default true. Switch only if really needed"
        ),
    ] = True,
) -> Dict[str, Any]:
    """
    Get detailed information about a specific device.

    Args:
        device_id: The unique identifier of the device.
        compact: Optional switch for compact results, by default true. Switch only if really needed

    Returns:
        Device details including capabilities, settings, and insights.
    """
    try:
        client = await ensure_client()

        # Get device details
        device = await client.devices.get_device(device_id)
        capabilities = await client.devices.get_device_capabilities(device_id)
        settings = await client.devices.get_device_settings(device_id)

        # Set up dumper based on compact flag
        if compact:
            dumper = attrgetter("model_dump_compact")
        else:
            dumper = attrgetter("model_dump")

        # Convert to dictionary
        device_dict = dumper(device)()
        device_dict["is_online"] = device.is_online()
        device_dict["driver_id"] = device.get_driver_id()
        device_dict["zone_id"] = device.get_zone_id()
        device_dict["capabilities_detailed"] = {
            cap_id: cap.model_dump() for cap_id, cap in capabilities.items()
        }
        device_dict["settings_detailed"] = settings

        return {"device": device_dict}

    except Exception as e:
        logger.error(f"Error getting device {device_id}: {e}")
        return {"error": f"Failed to get device: {e}"}


@mcp.tool()
async def get_devices_classes() -> Dict[str, Any]:
    """
    List all possible device clasess, usefull for getting know what to look for
    Usually better to query it before searching by name first

    Returns:
        All available device classes
    """
    try:
        client = await ensure_client()
        classes = await client.devices.get_device_classes()
        return {"classes": classes}
    except Exception as e:
        logger.error(f"Error listing devices clases: {e}")
        return {"error": f"Failed to get devices classes: {e}"}


@mcp.tool()
async def get_devices_capabilities() -> Dict[str, Any]:
    """
    List all possible device capabilities, usefull for getting know what to look for.
    Usually better to query it before searching by name first

    Returns:
        All available device capabilities
    """
    try:
        client = await ensure_client()
        classes = await client.devices.get_devices_capabilities()
        return {"capabilities": classes}
    except Exception as e:
        logger.error(f"Error listing devices capabilities: {e}")
        return {"error": f"Failed to get devices capabilities: {e}"}


@mcp.tool()
async def search_devices_by_name(
    query: str,
    cursor: Optional[str] = None,
    compact: Annotated[
        bool,
        Field(
            description="Optional switch for compact results, by default true. Switch only if really needed"
        ),
    ] = True,
) -> Dict[str, Any]:
    """
    Search devices by name with pagination support.

    Args:
        query: Search query to match against device names.
        cursor: Optional cursor for pagination.
        compact: Optional switch for compact results, by default true. Switch only if really needed

    Returns:
        Paginated list of matching devices.
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()

        # Search devices
        devices = await client.devices.search_devices_by_name(query)

        # Convert to dictionaries
        # Set up dumper based on compact flag
        if compact:
            dumper = attrgetter("model_dump_compact")
        else:
            dumper = attrgetter("model_dump")

        # Convert to dictionaries for serialization
        device_dicts = []
        for device in devices:
            device_dict = dumper(device)()
            device_dict["is_online"] = device.is_online()
            device_dict["driver_id"] = device.get_driver_id()
            device_dict["zone_id"] = device.get_zone_id()
            device_dicts.append(device_dict)

        # Apply pagination
        result = paginate_results(device_dicts, cursor_params)

        return {
            "devices": result["items"],
            "query": query,
            "pagination": {
                "total_count": result["total_count"],
                "page_size": result["page_size"],
                "offset": result["offset"],
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
            },
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error searching devices: {e}")
        return {"error": f"Failed to search devices: {e}"}


@mcp.tool()
async def search_devices_by_class(
    query: str,
    cursor: Optional[str] = None,
    compact: Annotated[
        bool,
        Field(
            description="Optional switch for compact results, by default true. Switch only if really needed"
        ),
    ] = True,
) -> Dict[str, Any]:
    """
    Search devices by class with pagination support.

    Args:
        query: Search query to match against device class.
        cursor: Optional cursor for pagination.
        compact: Optional switch for compact results, by default true. Switch only if really needed

    Returns:
        Paginated list of matching devices.
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()

        # Search devices
        devices = await client.devices.search_devices_by_class(query)

        # Convert to dictionaries
        # Set up dumper based on compact flag
        if compact:
            dumper = attrgetter("model_dump_compact")
        else:
            dumper = attrgetter("model_dump")

        # Convert to dictionaries for serialization
        device_dicts = []
        for device in devices:
            device_dict = dumper(device)()
            device_dict["is_online"] = device.is_online()
            device_dict["driver_id"] = device.get_driver_id()
            device_dict["zone_id"] = device.get_zone_id()
            device_dicts.append(device_dict)

        # Apply pagination
        result = paginate_results(device_dicts, cursor_params)

        return {
            "devices": result["items"],
            "query": query,
            "pagination": {
                "total_count": result["total_count"],
                "page_size": result["page_size"],
                "offset": result["offset"],
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
            },
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error searching devices: {e}")
        return {"error": f"Failed to search devices: {e}"}


@mcp.tool()
async def control_device(
    device_id: str, capability: str, value: Union[bool, int, float, str]
) -> Dict[str, Any]:
    """
    Control a device by setting a capability value.

    Args:
        device_id: The unique identifier of the device.
        capability: The capability to control (e.g., 'onoff', 'dim', 'target_temperature').
        value: The value to set for the capability, must to be valid JSON value.

    Returns:
        Success status and current device state.
    """
    try:
        client = await ensure_client()

        if isinstance(value, str):
            try:
                # it's a workaround for some tools not setting the value properly as JSON
                value = json.loads(value)  # TODO potentially unsafe place,
            except json.decoder.JSONDecodeError:
                # let's assume that the value was meant to be as is
                pass

        # Set capability value
        success = await client.devices.set_capability_value(
            device_id, capability, value
        )

        if success:
            # Get updated device state
            device = await client.devices.get_device(device_id)
            current_value = device.get_capability_value(capability)

            return {
                "success": True,
                "device_id": device_id,
                "capability": capability,
                "requested_value": value,
                "current_value": current_value,
                "device_name": device.name,
            }
        else:
            return {
                "success": False,
                "error": "Failed to set capability value",
                "device_id": device_id,
                "capability": capability,
                "requested_value": value,
            }

    except Exception as e:
        logger.error(f"Error controlling device {device_id}: {e}")
        return {"error": f"Failed to control device: {e}"}


@mcp.tool()
async def list_zones(cursor: Optional[str] = None) -> Dict[str, Any]:
    """
    List all zones with pagination support.

    Args:
        cursor: Optional cursor for pagination.

    Returns:
        Paginated list of zones.
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()

        # Get all zones
        zones = await client.zones.get_zones()

        # Convert to dictionaries
        zone_dicts = [zone.model_dump() for zone in zones]

        # Apply pagination
        result = paginate_results(zone_dicts, cursor_params)

        return {
            "zones": result["items"],
            "pagination": {
                "total_count": result["total_count"],
                "page_size": result["page_size"],
                "offset": result["offset"],
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
            },
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error listing zones: {e}")
        return {"error": f"Failed to list zones: {e}"}


@mcp.tool()
async def get_zone_devices(
    zone_id: str,
    cursor: Optional[str] = None,
    compact: Annotated[
        bool,
        Field(
            description="Optional switch for compact results, by default true. Switch only if really needed"
        ),
    ] = True,
) -> Dict[str, Any]:
    """
    Get all devices in a specific zone with pagination support.

    Args:
        zone_id: The unique identifier of the zone.
        cursor: Optional cursor for pagination.
        compact: Optional switch for compact results, by default true. Switch only if really needed

    Returns:
        Paginated list of devices in the zone.
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()

        # Get devices in zone
        devices = await client.devices.get_devices_by_zone(zone_id)

        # Convert to dictionaries
        # Set up dumper based on compact flag
        if compact:
            dumper = attrgetter("model_dump_compact")
        else:
            dumper = attrgetter("model_dump")

        # Convert to dictionaries for serialization
        device_dicts = []
        for device in devices:
            device_dict = dumper(device)()
            device_dict["is_online"] = device.is_online()
            device_dicts.append(device_dict)

        # Apply pagination
        result = paginate_results(device_dicts, cursor_params)

        return {
            "devices": result["items"],
            "zone_id": zone_id,
            "pagination": {
                "total_count": result["total_count"],
                "page_size": result["page_size"],
                "offset": result["offset"],
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
            },
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error getting zone devices: {e}")
        return {"error": f"Failed to get zone devices: {e}"}


@mcp.tool()
async def list_flows(cursor: Optional[str] = None) -> Dict[str, Any]:
    """
    List all flows with pagination support.

    Args:
        cursor: Optional cursor for pagination.

    Returns:
        Paginated list of flows.
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()

        # Get all flows
        flows = await client.flows.get_flows()

        # Convert to dictionaries
        flow_dicts = [flow.model_dump() for flow in flows]

        # Apply pagination
        result = paginate_results(flow_dicts, cursor_params)

        return {
            "flows": result["items"],
            "pagination": {
                "total_count": result["total_count"],
                "page_size": result["page_size"],
                "offset": result["offset"],
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
            },
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error listing flows: {e}")
        return {"error": f"Failed to list flows: {e}"}


@mcp.tool()
async def trigger_flow(flow_id: str) -> Dict[str, Any]:
    """
    Trigger a specific flow.

    Args:
        flow_id: The unique identifier of the flow to trigger.

    Returns:
        Success status and flow information.
    """
    try:
        client = await ensure_client()

        # Trigger the flow
        success = await client.flows.trigger_flow(flow_id)

        if success:
            # Get flow details
            flow = await client.flows.get_flow(flow_id)
            return {
                "success": True,
                "flow_id": flow_id,
                "flow_name": flow.name,
                "flow_type": flow.type if hasattr(flow, "type") else "unknown",
            }
        else:
            return {
                "success": False,
                "error": "Failed to trigger flow",
                "flow_id": flow_id,
            }

    except Exception as e:
        logger.error(f"Error triggering flow {flow_id}: {e}")
        return {"error": f"Failed to trigger flow: {e}"}


@mcp.tool()
async def list_advanced_flows(cursor: Optional[str] = None) -> Dict[str, Any]:
    """
    List all advanced flows with pagination support.

    Args:
        cursor: Optional cursor for pagination.

    Returns:
        Paginated list of advanced flows.
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()

        # Get all advanced flows
        advanced_flows = await client.flows.get_advanced_flows()

        # Convert to dictionaries
        flow_dicts = [flow.model_dump() for flow in advanced_flows]

        # Apply pagination
        result = paginate_results(flow_dicts, cursor_params)

        return {
            "advanced_flows": result["items"],
            "pagination": {
                "total_count": result["total_count"],
                "page_size": result["page_size"],
                "offset": result["offset"],
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
            },
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error listing advanced flows: {e}")
        return {"error": f"Failed to list advanced flows: {e}"}


@mcp.tool()
async def get_advanced_flow(flow_id: str) -> Dict[str, Any]:
    """
    Get details of a specific advanced flow.

    Args:
        flow_id: The unique identifier of the advanced flow.

    Returns:
        Advanced flow details.
    """
    try:
        client = await ensure_client()

        # Get the advanced flow
        flow = await client.flows.get_advanced_flow(flow_id)

        return {
            "advanced_flow": flow.model_dump(),
        }

    except Exception as e:
        logger.error(f"Error getting advanced flow {flow_id}: {e}")
        return {"error": f"Failed to get advanced flow: {e}"}


@mcp.tool()
async def trigger_advanced_flow(flow_id: str) -> Dict[str, Any]:
    """
    Trigger a specific advanced flow.

    Args:
        flow_id: The unique identifier of the advanced flow to trigger.

    Returns:
        Success status and advanced flow information.
    """
    try:
        client = await ensure_client()

        # Trigger the advanced flow
        success = await client.flows.trigger_advanced_flow(flow_id)

        if success:
            # Get advanced flow details
            flow = await client.flows.get_advanced_flow(flow_id)
            return {
                "success": True,
                "flow_id": flow_id,
                "flow_name": flow.name,
                "flow_type": "advanced",
            }
        else:
            return {
                "success": False,
                "error": "Failed to trigger advanced flow",
                "flow_id": flow_id,
            }

    except Exception as e:
        logger.error(f"Error triggering advanced flow {flow_id}: {e}")
        return {"error": f"Failed to trigger advanced flow: {e}"}


@mcp.tool()
async def search_advanced_flows(
    query: str, cursor: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search advanced flows by name or description.

    Args:
        query: Search query string.
        cursor: Optional cursor for pagination.

    Returns:
        Paginated list of matching advanced flows.
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()

        # Search advanced flows
        advanced_flows = await client.flows.search_advanced_flows(query)

        # Convert to dictionaries
        flow_dicts = [flow.model_dump() for flow in advanced_flows]

        # Apply pagination
        result = paginate_results(flow_dicts, cursor_params)

        return {
            "advanced_flows": result["items"],
            "query": query,
            "pagination": {
                "total_count": result["total_count"],
                "page_size": result["page_size"],
                "offset": result["offset"],
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
            },
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error searching advanced flows with query '{query}': {e}")
        return {"error": f"Failed to search advanced flows: {e}"}


@mcp.tool()
async def get_enabled_advanced_flows(cursor: Optional[str] = None) -> Dict[str, Any]:
    """
    Get all enabled advanced flows.

    Args:
        cursor: Optional cursor for pagination.

    Returns:
        Paginated list of enabled advanced flows.
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()

        # Get enabled advanced flows
        advanced_flows = await client.flows.get_enabled_advanced_flows()

        # Convert to dictionaries
        flow_dicts = [flow.model_dump() for flow in advanced_flows]

        # Apply pagination
        result = paginate_results(flow_dicts, cursor_params)

        return {
            "enabled_advanced_flows": result["items"],
            "pagination": {
                "total_count": result["total_count"],
                "page_size": result["page_size"],
                "offset": result["offset"],
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
            },
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error getting enabled advanced flows: {e}")
        return {"error": f"Failed to get enabled advanced flows: {e}"}


@mcp.tool()
async def get_disabled_advanced_flows(cursor: Optional[str] = None) -> Dict[str, Any]:
    """
    Get all disabled advanced flows.

    Args:
        cursor: Optional cursor for pagination.

    Returns:
        Paginated list of disabled advanced flows.
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()

        # Get disabled advanced flows
        advanced_flows = await client.flows.get_disabled_advanced_flows()

        # Convert to dictionaries
        flow_dicts = [flow.model_dump() for flow in advanced_flows]

        # Apply pagination
        result = paginate_results(flow_dicts, cursor_params)

        return {
            "disabled_advanced_flows": result["items"],
            "pagination": {
                "total_count": result["total_count"],
                "page_size": result["page_size"],
                "offset": result["offset"],
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
            },
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error getting disabled advanced flows: {e}")
        return {"error": f"Failed to get disabled advanced flows: {e}"}


@mcp.tool()
async def get_broken_advanced_flows(cursor: Optional[str] = None) -> Dict[str, Any]:
    """
    Get all broken advanced flows.

    Args:
        cursor: Optional cursor for pagination.

    Returns:
        Paginated list of broken advanced flows.
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()

        # Get broken advanced flows
        advanced_flows = await client.flows.get_broken_advanced_flows()

        # Convert to dictionaries
        flow_dicts = [flow.model_dump() for flow in advanced_flows]

        # Apply pagination
        result = paginate_results(flow_dicts, cursor_params)

        return {
            "broken_advanced_flows": result["items"],
            "pagination": {
                "total_count": result["total_count"],
                "page_size": result["page_size"],
                "offset": result["offset"],
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
            },
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error getting broken advanced flows: {e}")
        return {"error": f"Failed to get broken advanced flows: {e}"}


@mcp.tool()
async def get_advanced_flows_by_folder(
    folder_id: str, cursor: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get advanced flows in a specific folder.

    Args:
        folder_id: The unique identifier of the folder.
        cursor: Optional cursor for pagination.

    Returns:
        Paginated list of advanced flows in the folder.
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()

        # Get advanced flows by folder
        advanced_flows = await client.flows.get_advanced_flows_by_folder(folder_id)

        # Convert to dictionaries
        flow_dicts = [flow.model_dump() for flow in advanced_flows]

        # Apply pagination
        result = paginate_results(flow_dicts, cursor_params)

        return {
            "advanced_flows": result["items"],
            "folder_id": folder_id,
            "pagination": {
                "total_count": result["total_count"],
                "page_size": result["page_size"],
                "offset": result["offset"],
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
            },
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error getting advanced flows by folder {folder_id}: {e}")
        return {"error": f"Failed to get advanced flows by folder: {e}"}


@mcp.tool()
async def get_advanced_flows_without_folder(
    cursor: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get advanced flows without a folder.

    Args:
        cursor: Optional cursor for pagination.

    Returns:
        Paginated list of advanced flows without a folder.
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()

        # Get advanced flows without folder
        advanced_flows = await client.flows.get_advanced_flows_without_folder()

        # Convert to dictionaries
        flow_dicts = [flow.model_dump() for flow in advanced_flows]

        # Apply pagination
        result = paginate_results(flow_dicts, cursor_params)

        return {
            "advanced_flows": result["items"],
            "pagination": {
                "total_count": result["total_count"],
                "page_size": result["page_size"],
                "offset": result["offset"],
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
            },
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error getting advanced flows without folder: {e}")
        return {"error": f"Failed to get advanced flows without folder: {e}"}


@mcp.tool()
async def get_advanced_flows_with_inline_scripts(
    cursor: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get advanced flows that contain inline scripts.

    Args:
        cursor: Optional cursor for pagination.

    Returns:
        Paginated list of advanced flows with inline scripts.
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()

        # Get advanced flows with inline scripts
        advanced_flows = await client.flows.get_advanced_flows_with_inline_scripts()

        # Convert to dictionaries
        flow_dicts = [flow.model_dump() for flow in advanced_flows]

        # Apply pagination
        result = paginate_results(flow_dicts, cursor_params)

        return {
            "advanced_flows": result["items"],
            "pagination": {
                "total_count": result["total_count"],
                "page_size": result["page_size"],
                "offset": result["offset"],
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
            },
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error getting advanced flows with inline scripts: {e}")
        return {"error": f"Failed to get advanced flows with inline scripts: {e}"}


@mcp.tool()
async def enable_advanced_flow(flow_id: str) -> Dict[str, Any]:
    """
    Enable a specific advanced flow.

    Args:
        flow_id: The unique identifier of the advanced flow to enable.

    Returns:
        Success status and flow information.
    """
    try:
        client = await ensure_client()

        # Enable the advanced flow
        success = await client.flows.enable_advanced_flow(flow_id)

        if success:
            # Get advanced flow details
            flow = await client.flows.get_advanced_flow(flow_id)
            return {
                "success": True,
                "flow_id": flow_id,
                "flow_name": flow.name,
                "action": "enabled",
            }
        else:
            return {
                "success": False,
                "error": "Failed to enable advanced flow",
                "flow_id": flow_id,
            }

    except Exception as e:
        logger.error(f"Error enabling advanced flow {flow_id}: {e}")
        return {"error": f"Failed to enable advanced flow: {e}"}


@mcp.tool()
async def disable_advanced_flow(flow_id: str) -> Dict[str, Any]:
    """
    Disable a specific advanced flow.

    Args:
        flow_id: The unique identifier of the advanced flow to disable.

    Returns:
        Success status and flow information.
    """
    try:
        client = await ensure_client()

        # Disable the advanced flow
        success = await client.flows.disable_advanced_flow(flow_id)

        if success:
            # Get advanced flow details
            flow = await client.flows.get_advanced_flow(flow_id)
            return {
                "success": True,
                "flow_id": flow_id,
                "flow_name": flow.name,
                "action": "disabled",
            }
        else:
            return {
                "success": False,
                "error": "Failed to disable advanced flow",
                "flow_id": flow_id,
            }

    except Exception as e:
        logger.error(f"Error disabling advanced flow {flow_id}: {e}")
        return {"error": f"Failed to disable advanced flow: {e}"}


@mcp.tool()
async def get_flow_folders() -> Dict[str, Any]:
    """
    Get all flow folders.

    Returns:
        List of flow folders.
    """
    try:
        client = await ensure_client()

        # Get all flow folders
        folders = await client.flows.get_flow_folders()

        return {
            "folders": folders,
        }

    except Exception as e:
        logger.error(f"Error getting flow folders: {e}")
        return {"error": f"Failed to get flow folders: {e}"}


@mcp.tool()
async def get_flows_by_folder(
    folder_id: str, cursor: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get flows in a specific folder.

    Args:
        folder_id: The unique identifier of the folder.
        cursor: Optional cursor for pagination.

    Returns:
        Paginated list of flows in the folder.
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()

        # Get flows by folder
        flows = await client.flows.get_flows_by_folder(folder_id)

        # Convert to dictionaries
        flow_dicts = [flow.model_dump() for flow in flows]

        # Apply pagination
        result = paginate_results(flow_dicts, cursor_params)

        return {
            "flows": result["items"],
            "folder_id": folder_id,
            "pagination": {
                "total_count": result["total_count"],
                "page_size": result["page_size"],
                "offset": result["offset"],
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
            },
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error getting flows by folder {folder_id}: {e}")
        return {"error": f"Failed to get flows by folder: {e}"}


@mcp.tool()
async def get_flows_without_folder(cursor: Optional[str] = None) -> Dict[str, Any]:
    """
    Get flows without a folder.

    Args:
        cursor: Optional cursor for pagination.

    Returns:
        Paginated list of flows without a folder.
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()

        # Get flows without folder
        flows = await client.flows.get_flows_without_folder()

        # Convert to dictionaries
        flow_dicts = [flow.model_dump() for flow in flows]

        # Apply pagination
        result = paginate_results(flow_dicts, cursor_params)

        return {
            "flows": result["items"],
            "pagination": {
                "total_count": result["total_count"],
                "page_size": result["page_size"],
                "offset": result["offset"],
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
            },
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error getting flows without folder: {e}")
        return {"error": f"Failed to get flows without folder: {e}"}


@mcp.tool()
async def get_device_insights(
    device_id: str,
    capability: str,
    resolution: Annotated[
        Literal[
            "lastHour",
            "last6Hours",
            "last12Hours",
            "last24Hours",
            "last7Days",
            "last14Days",
            "last31Days",
        ],
        Field(description="Resolution for insights"),
    ],
    from_timestamp: Annotated[
        int | None, Field(description="Timestamp to start insights from")
    ] = None,
    to_timestamp: Annotated[
        int | None, Field(description="Timestamp to end insights on")
    ] = None,
) -> Dict[str, Any]:
    """
    Get insights data for a specific device with pagination support.

    Args:
        device_id: The unique identifier of the device.
        cursor: Optional cursor for pagination.

    Returns:
        Paginated insights data for the device.
    """
    try:
        client = await ensure_client()

        # Get device insights
        insights = await client.devices.get_device_insights(
            device_id, capability, resolution, from_timestamp, to_timestamp
        )

        return {
            "insights": insights,
            "device_id": device_id,
        }

    except PaginationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error getting device insights: {e}")
        return {"error": f"Failed to get device insights: {e}"}


@mcp.tool()
async def get_zone_temp(zone_id: str) -> Dict[str, Any]:
    """
    Get zone temperature by averaging applicable devices measure_temperature in the zone

    Args:
        zone_id: Zone id

    Returns:
        Temperature in the zone

    """
    try:
        client = await ensure_client()
        temp = await client.zones.get_zone_temperature(zone_id)
        return {"temperature": temp}
    except Exception as e:
        logger.error(f"Error getting zone temperature: {e}")
        return {"error": f"Failed getting zone temperature: {e}"}


@mcp.tool()
async def get_system_info() -> Dict[str, Any]:
    """
    Get basic system information about the Homey instance. Includes location, address, language, units, connection status, and counts of devices, zones, and flows.
    Usefull to use before other methods/tools.

    Returns:
        System information
    """
    try:
        client = await ensure_client()

        # Get basic counts
        devices = await client.devices.get_devices()
        zones = await client.zones.get_zones()
        flows = await client.flows.get_flows()

        # Count online/offline devices
        online_devices = len([d for d in devices if d.is_online()])
        offline_devices = len(devices) - online_devices

        # Count enabled/disabled flows
        enabled_flows = await client.flows.get_enabled_flows()
        disabled_flows = await client.flows.get_disabled_flows()

        # Advanced flows
        advanced_flows = await client.flows.get_advanced_flows()
        enabled_advanced_flows = await client.flows.get_enabled_advanced_flows()
        disabled_advanced_flows = await client.flows.get_disabled_advanced_flows()

        client = await ensure_client()
        config = await client.system.get_system_config()

        return {
            "connection_status": "connected",
            "total_devices": len(devices),
            "online_devices": online_devices,
            "offline_devices": offline_devices,
            "total_zones": len(zones),
            "total_flows": len(flows) + len(advanced_flows),
            "enabled_flows": len(enabled_flows),
            "disabled_flows": len(disabled_flows),
            "enabled_advanced_flows": len(enabled_advanced_flows),
            "disabled_advanced_flows": len(disabled_advanced_flows),
            "address": config.address,
            "language": config.language,
            "units": config.units,
            "units_metric": config.is_metric(),
            "units_imperial": config.is_imperial(),
            "location": config.get_location_coordinates(),
        }

    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {"error": f"Failed to get system info: {e}"}


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
        global homey_client
        if homey_client:
            try:
                await homey_client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting client: {e}")


if __name__ == "__main__":
    asyncio.run(main())
