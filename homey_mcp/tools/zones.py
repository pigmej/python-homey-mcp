"""Zone-related tools for HomeyPro MCP Server."""

from operator import attrgetter
from typing import Any, Dict, Optional
from typing_extensions import Annotated
from pydantic.fields import Field

from ..client.manager import ensure_client
from ..utils.logging import get_logger
from ..utils.pagination import paginate_results, parse_cursor, PaginationError
from ..mcp_instance import mcp

logger = get_logger(__name__)


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