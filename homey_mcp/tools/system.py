"""System-related tools for HomeyPro MCP Server."""

from typing import Any, Dict

from ..client.manager import ensure_client
from ..utils.logging import get_logger
from ..mcp_instance import mcp

logger = get_logger(__name__)


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