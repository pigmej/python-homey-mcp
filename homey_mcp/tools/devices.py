"""Device-related tools for HomeyPro MCP Server."""

import json
from operator import attrgetter
from typing import Any, Dict, Optional, Union
from typing_extensions import Annotated, Literal
from pydantic.fields import Field

from ..client.manager import ensure_client
from ..utils.logging import get_logger
from ..utils.pagination import paginate_results, parse_cursor, PaginationError
from ..mcp_instance import mcp

logger = get_logger(__name__)


# resource would be better but Gemini does not support it
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
            if device.hidden:
                # omit hidden devices
                continue
            device_dict = dumper(device)()
            # Add computed fields
            device_dict["is_online"] = device.is_online()
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
        logger.error(f"Pagination error in list_devices: {e}")
        return {
            "error": f"Pagination error: {str(e)}",
            "error_type": "pagination",
            "suggested_action": "Check cursor parameter format"
        }
    except ConnectionError as e:
        logger.error(f"Connection error in list_devices: {e}")
        return {
            "error": "Failed to list devices due to connection issues",
            "error_type": "connection",
            "suggested_action": "Check HomeyPro connectivity and network settings",
            "details": str(e)
        }
    except TimeoutError as e:
        logger.error(f"Timeout error in list_devices: {e}")
        return {
            "error": "Failed to list devices due to timeout",
            "error_type": "timeout",
            "suggested_action": "HomeyPro may be overloaded, try again in a few moments",
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in list_devices: {type(e).__name__}: {e}")
        return {
            "error": "Failed to list devices due to unexpected error",
            "error_type": "unknown",
            "suggested_action": "Check system logs and HomeyPro status",
            "details": f"{type(e).__name__}: {str(e)}"
        }


# resource would be better but Gemini does not support it
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
        device_dict["capabilities_detailed"] = {
            cap_id: cap.model_dump() for cap_id, cap in capabilities.items()
        }
        device_dict["settings_detailed"] = settings

        return {"device": device_dict}

    except ConnectionError as e:
        logger.error(f"Connection error in get_device {device_id}: {e}")
        return {
            "error": "Failed to get device due to connection issues",
            "error_type": "connection",
            "suggested_action": "Check HomeyPro connectivity and network settings",
            "device_id": device_id,
            "details": str(e)
        }
    except TimeoutError as e:
        logger.error(f"Timeout error in get_device {device_id}: {e}")
        return {
            "error": "Failed to get device due to timeout",
            "error_type": "timeout",
            "suggested_action": "HomeyPro may be overloaded, try again in a few moments",
            "device_id": device_id,
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_device {device_id}: {type(e).__name__}: {e}")
        return {
            "error": "Failed to get device due to unexpected error",
            "error_type": "unknown",
            "suggested_action": "Check system logs and HomeyPro status",
            "device_id": device_id,
            "details": f"{type(e).__name__}: {str(e)}"
        }


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
    except ConnectionError as e:
        logger.error(f"Connection error in get_devices_classes: {e}")
        return {
            "error": "Failed to get device classes due to connection issues",
            "error_type": "connection",
            "suggested_action": "Check HomeyPro connectivity and network settings",
            "details": str(e)
        }
    except TimeoutError as e:
        logger.error(f"Timeout error in get_devices_classes: {e}")
        return {
            "error": "Failed to get device classes due to timeout",
            "error_type": "timeout",
            "suggested_action": "HomeyPro may be overloaded, try again in a few moments",
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_devices_classes: {type(e).__name__}: {e}")
        return {
            "error": "Failed to get device classes due to unexpected error",
            "error_type": "unknown",
            "suggested_action": "Check system logs and HomeyPro status",
            "details": f"{type(e).__name__}: {str(e)}"
        }


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
    except ConnectionError as e:
        logger.error(f"Connection error in get_devices_capabilities: {e}")
        return {
            "error": "Failed to get device capabilities due to connection issues",
            "error_type": "connection",
            "suggested_action": "Check HomeyPro connectivity and network settings",
            "details": str(e)
        }
    except TimeoutError as e:
        logger.error(f"Timeout error in get_devices_capabilities: {e}")
        return {
            "error": "Failed to get device capabilities due to timeout",
            "error_type": "timeout",
            "suggested_action": "HomeyPro may be overloaded, try again in a few moments",
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_devices_capabilities: {type(e).__name__}: {e}")
        return {
            "error": "Failed to get device capabilities due to unexpected error",
            "error_type": "unknown",
            "suggested_action": "Check system logs and HomeyPro status",
            "details": f"{type(e).__name__}: {str(e)}"
        }


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
    Search devices by name with pagination support. Using note field from the result could be helpful too.

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
            if device.hidden:
                # omit hidden devices
                continue
            device_dict = dumper(device)()
            device_dict["is_online"] = device.is_online()
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
        logger.error(f"Pagination error in search_devices_by_name: {e}")
        return {
            "error": f"Pagination error: {str(e)}",
            "error_type": "pagination",
            "suggested_action": "Check cursor parameter format",
            "query": query
        }
    except ConnectionError as e:
        logger.error(f"Connection error in search_devices_by_name: {e}")
        return {
            "error": "Failed to search devices due to connection issues",
            "error_type": "connection",
            "suggested_action": "Check HomeyPro connectivity and network settings",
            "query": query,
            "details": str(e)
        }
    except TimeoutError as e:
        logger.error(f"Timeout error in search_devices_by_name: {e}")
        return {
            "error": "Failed to search devices due to timeout",
            "error_type": "timeout",
            "suggested_action": "HomeyPro may be overloaded, try again in a few moments",
            "query": query,
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in search_devices_by_name: {type(e).__name__}: {e}")
        return {
            "error": "Failed to search devices due to unexpected error",
            "error_type": "unknown",
            "suggested_action": "Check system logs and HomeyPro status",
            "query": query,
            "details": f"{type(e).__name__}: {str(e)}"
        }


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
            if device.hidden:
                # omit hidden devices
                continue
            device_dict = dumper(device)()
            device_dict["is_online"] = device.is_online()
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
        logger.error(f"Pagination error in search_devices_by_class: {e}")
        return {
            "error": f"Pagination error: {str(e)}",
            "error_type": "pagination",
            "suggested_action": "Check cursor parameter format",
            "query": query
        }
    except ConnectionError as e:
        logger.error(f"Connection error in search_devices_by_class: {e}")
        return {
            "error": "Failed to search devices due to connection issues",
            "error_type": "connection",
            "suggested_action": "Check HomeyPro connectivity and network settings",
            "query": query,
            "details": str(e)
        }
    except TimeoutError as e:
        logger.error(f"Timeout error in search_devices_by_class: {e}")
        return {
            "error": "Failed to search devices due to timeout",
            "error_type": "timeout",
            "suggested_action": "HomeyPro may be overloaded, try again in a few moments",
            "query": query,
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in search_devices_by_class: {type(e).__name__}: {e}")
        return {
            "error": "Failed to search devices due to unexpected error",
            "error_type": "unknown",
            "suggested_action": "Check system logs and HomeyPro status",
            "query": query,
            "details": f"{type(e).__name__}: {str(e)}"
        }


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

    except ConnectionError as e:
        logger.error(f"Connection error in control_device {device_id}: {e}")
        return {
            "error": "Failed to control device due to connection issues",
            "error_type": "connection",
            "suggested_action": "Check HomeyPro connectivity and network settings",
            "device_id": device_id,
            "capability": capability,
            "requested_value": value,
            "details": str(e)
        }
    except TimeoutError as e:
        logger.error(f"Timeout error in control_device {device_id}: {e}")
        return {
            "error": "Failed to control device due to timeout",
            "error_type": "timeout",
            "suggested_action": "HomeyPro may be overloaded, try again in a few moments",
            "device_id": device_id,
            "capability": capability,
            "requested_value": value,
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in control_device {device_id}: {type(e).__name__}: {e}")
        return {
            "error": "Failed to control device due to unexpected error",
            "error_type": "unknown",
            "suggested_action": "Check system logs and HomeyPro status",
            "device_id": device_id,
            "capability": capability,
            "requested_value": value,
            "details": f"{type(e).__name__}: {str(e)}"
        }


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
        capability: The capability to get insights for.
        resolution: Resolution for insights.
        from_timestamp: Timestamp to start insights from.
        to_timestamp: Timestamp to end insights on.

    Returns:
        Insights data for the device.
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
        logger.error(f"Pagination error in get_device_insights: {e}")
        return {
            "error": f"Pagination error: {str(e)}",
            "error_type": "pagination",
            "suggested_action": "Check pagination parameters",
            "device_id": device_id,
            "capability": capability
        }
    except ConnectionError as e:
        logger.error(f"Connection error in get_device_insights {device_id}: {e}")
        return {
            "error": "Failed to get device insights due to connection issues",
            "error_type": "connection",
            "suggested_action": "Check HomeyPro connectivity and network settings",
            "device_id": device_id,
            "capability": capability,
            "details": str(e)
        }
    except TimeoutError as e:
        logger.error(f"Timeout error in get_device_insights {device_id}: {e}")
        return {
            "error": "Failed to get device insights due to timeout",
            "error_type": "timeout",
            "suggested_action": "HomeyPro may be overloaded, try again in a few moments",
            "device_id": device_id,
            "capability": capability,
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_device_insights {device_id}: {type(e).__name__}: {e}")
        return {
            "error": "Failed to get device insights due to unexpected error",
            "error_type": "unknown",
            "suggested_action": "Check system logs and HomeyPro status",
            "device_id": device_id,
            "capability": capability,
            "details": f"{type(e).__name__}: {str(e)}"
        }
