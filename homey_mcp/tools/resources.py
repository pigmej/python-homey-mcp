"""Resource-related tools for HomeyPro MCP Server."""

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from ..client.manager import ensure_client
from ..utils.logging import get_logger
from ..mcp_instance import mcp

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with timestamp and TTL tracking."""
    data: Any
    timestamp: float
    ttl: float
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() > (self.timestamp + self.ttl)


class SimpleCache:
    """Simple in-memory cache with TTL-based expiration logic."""
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
    
    async def get_or_fetch(self, key: str, fetcher: Callable, ttl: float) -> Any:
        """
        Get data from cache or fetch it using the provided fetcher function.
        
        Args:
            key: Cache key
            fetcher: Async function to fetch data if not in cache or expired
            ttl: Time to live in seconds
            
        Returns:
            Cached or freshly fetched data
            
        Raises:
            Exception: If fetcher fails and no stale data is available
        """
        entry = self._cache.get(key)
        
        # Return fresh cache data if available and not expired
        if entry and not entry.is_expired():
            logger.debug(f"Cache hit for key: {key}")
            return entry.data
            
        # Try to fetch fresh data
        try:
            logger.debug(f"Cache miss or expired for key: {key}, fetching fresh data")
            data = await fetcher()
            self._cache[key] = CacheEntry(data, time.time(), ttl)
            logger.debug(f"Successfully cached fresh data for key: {key}")
            return data
        except ConnectionError as e:
            logger.warning(f"Connection error for {key}: {e}")
            if entry:
                logger.info(f"Using stale cache for {key} due to connection error")
                return {"data": entry.data, "is_stale": True, "error_type": "connection"}
            logger.error(f"Connection failed for {key} and no stale data available")
            raise
        except TimeoutError as e:
            logger.warning(f"Timeout error for {key}: {e}")
            if entry:
                logger.info(f"Using stale cache for {key} due to timeout")
                return {"data": entry.data, "is_stale": True, "error_type": "timeout"}
            logger.error(f"Timeout for {key} and no stale data available")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching data for {key}: {type(e).__name__}: {e}")
            # Return stale data if available as fallback
            if entry:
                logger.warning(f"Using stale cache for {key} due to unexpected error")
                return {"data": entry.data, "is_stale": True, "error_type": "unknown"}
            # No stale data available, re-raise the exception
            logger.error(f"Failed to fetch data for {key} and no stale data available")
            raise


# Global cache instance for resources
_resource_cache = SimpleCache()


@mcp.resource("homey://system/overview")
async def system_overview_resource() -> str:
    """
    Provides comprehensive system overview including device counts, zone counts, 
    and system health indicators.
    
    Returns:
        JSON string containing system overview data
    """
    async def fetch_system_overview():
        try:
            client = await ensure_client()
            
            # Fetch system configuration
            system_info = await client.system.get_system_config()
            
            # Fetch devices for counts and health indicators
            devices = await client.devices.get_devices()
            
            # Fetch zones for counts
            zones = await client.zones.get_zones()
            
            # Calculate device statistics
            total_devices = len(devices)
            online_devices = len([d for d in devices if hasattr(d, 'available') and d.available])
            device_types = set()
            total_capabilities = set()
            
            for device in devices:
                if hasattr(device, 'class_') and device.class_:
                    device_types.add(device.class_)
                if hasattr(device, 'capabilities') and device.capabilities:
                    if isinstance(device.capabilities, dict):
                        total_capabilities.update(device.capabilities.keys())
                    elif isinstance(device.capabilities, list):
                        total_capabilities.update(device.capabilities)
            
            # Calculate zone statistics
            total_zones = len(zones)
            
            # Build system overview
            overview = {
                "system_info": {
                    "name": getattr(system_info, 'name', 'Unknown'),
                    "version": getattr(system_info, 'version', 'Unknown'),
                    "platform": getattr(system_info, 'platform', 'Unknown'),
                    "uptime": getattr(system_info, 'uptime', 0)
                },
                "device_summary": {
                    "total_count": total_devices,
                    "online_count": online_devices,
                    "offline_count": total_devices - online_devices,
                    "device_types_count": len(device_types),
                    "capabilities_count": len(total_capabilities),
                    "health_percentage": round((online_devices / total_devices * 100) if total_devices > 0 else 100, 1)
                },
                "zone_summary": {
                    "total_count": total_zones,
                    "zone_names": [getattr(zone, 'name', 'Unknown') for zone in zones[:10]]  # Limit to first 10
                },
                "timestamp": time.time(),
                "cache_info": {
                    "ttl_seconds": 300,  # 5 minutes
                    "data_type": "system_overview"
                }
            }
            
            logger.info(f"System overview generated: {total_devices} devices, {online_devices} online, {total_zones} zones")
            return overview
            
        except Exception as e:
            logger.error(f"Failed to fetch system overview: {e}")
            raise
    
    try:
        # Use 5-minute TTL for system configuration data
        data = await _resource_cache.get_or_fetch("system_overview", fetch_system_overview, 300)
        
        # Handle stale data response
        if isinstance(data, dict) and "is_stale" in data:
            stale_data = data["data"]
            stale_data["cache_info"]["is_stale"] = True
            stale_data["cache_info"]["stale_reason"] = "HomeyPro unreachable, using cached data"
            stale_data["cache_info"]["error_type"] = data.get("error_type", "unknown")
            logger.info(f"Returning stale system overview data due to {data.get('error_type', 'unknown')} error")
            return str(stale_data)
        
        logger.debug("Successfully retrieved fresh system overview data")
        return str(data)
        
    except ConnectionError as e:
        logger.error(f"System overview resource connection failed: {e}")
        return str({
            "error": "Failed to retrieve system overview due to connection issues",
            "error_type": "connection",
            "fallback_available": False,
            "suggested_action": "Check HomeyPro connectivity and network settings",
            "timestamp": time.time(),
            "details": str(e)
        })
    except TimeoutError as e:
        logger.error(f"System overview resource timeout: {e}")
        return str({
            "error": "Failed to retrieve system overview due to timeout",
            "error_type": "timeout",
            "fallback_available": False,
            "suggested_action": "HomeyPro may be overloaded, try again in a few moments",
            "timestamp": time.time(),
            "details": str(e)
        })
    except Exception as e:
        logger.error(f"System overview resource unexpected error: {type(e).__name__}: {e}")
        return str({
            "error": "Failed to retrieve system overview due to unexpected error",
            "error_type": "unknown",
            "fallback_available": False,
            "suggested_action": "Check system logs and HomeyPro status",
            "timestamp": time.time(),
            "details": f"{type(e).__name__}: {str(e)}"
        })


@mcp.resource("homey://devices/registry")
async def device_registry_resource() -> str:
    """
    Provides complete device inventory with current states, capabilities, 
    and online/offline indicators.
    
    Returns:
        JSON string containing device registry data
    """
    async def fetch_device_registry():
        try:
            client = await ensure_client()
            
            # Fetch all devices
            devices = await client.devices.get_devices()
            
            device_registry = {
                "devices": [],
                "summary": {
                    "total_count": len(devices),
                    "online_count": 0,
                    "offline_count": 0,
                    "device_types": set(),
                    "capabilities": set()
                },
                "timestamp": time.time(),
                "cache_info": {
                    "ttl_seconds": 30,  # 30 seconds for dynamic device data
                    "data_type": "device_registry"
                }
            }
            
            # Process each device
            for device in devices:
                device_info = {
                    "id": getattr(device, 'id', 'unknown'),
                    "name": getattr(device, 'name', 'Unknown Device'),
                    "zone": getattr(device, 'zone', None),
                    "class": getattr(device, 'class_', 'unknown'),
                    "available": getattr(device, 'available', False),
                    "capabilities": {},
                    "capability_values": {},
                    "energy": getattr(device, 'energy', None),
                    "settings": getattr(device, 'settings', {}),
                    "ui": getattr(device, 'ui', {})
                }
                
                # Track online/offline status
                if device_info["available"]:
                    device_registry["summary"]["online_count"] += 1
                else:
                    device_registry["summary"]["offline_count"] += 1
                
                # Track device types
                if device_info["class"]:
                    device_registry["summary"]["device_types"].add(device_info["class"])
                
                # Process capabilities
                if hasattr(device, 'capabilities') and device.capabilities:
                    if isinstance(device.capabilities, dict):
                        device_info["capabilities"] = device.capabilities
                        device_registry["summary"]["capabilities"].update(device.capabilities.keys())
                    elif isinstance(device.capabilities, list):
                        device_info["capabilities"] = {cap: True for cap in device.capabilities}
                        device_registry["summary"]["capabilities"].update(device.capabilities)
                
                # Get capability values if available
                if hasattr(device, 'capabilitiesObj') and device.capabilitiesObj:
                    for cap_id, cap_obj in device.capabilitiesObj.items():
                        if hasattr(cap_obj, 'value'):
                            device_info["capability_values"][cap_id] = cap_obj.value
                
                device_registry["devices"].append(device_info)
            
            # Convert sets to lists for JSON serialization
            device_registry["summary"]["device_types"] = list(device_registry["summary"]["device_types"])
            device_registry["summary"]["capabilities"] = list(device_registry["summary"]["capabilities"])
            
            logger.info(f"Device registry generated: {len(devices)} devices, "
                       f"{device_registry['summary']['online_count']} online")
            return device_registry
            
        except Exception as e:
            logger.error(f"Failed to fetch device registry: {e}")
            raise
    
    try:
        # Use 30-second TTL for dynamic device data
        data = await _resource_cache.get_or_fetch("device_registry", fetch_device_registry, 30)
        
        # Handle stale data response
        if isinstance(data, dict) and "is_stale" in data:
            stale_data = data["data"]
            stale_data["cache_info"]["is_stale"] = True
            stale_data["cache_info"]["stale_reason"] = "HomeyPro unreachable, using cached data"
            stale_data["cache_info"]["error_type"] = data.get("error_type", "unknown")
            logger.info(f"Returning stale device registry data due to {data.get('error_type', 'unknown')} error")
            return str(stale_data)
        
        logger.debug("Successfully retrieved fresh device registry data")
        return str(data)
        
    except ConnectionError as e:
        logger.error(f"Device registry resource connection failed: {e}")
        return str({
            "error": "Failed to retrieve device registry due to connection issues",
            "error_type": "connection",
            "fallback_available": False,
            "suggested_action": "Check HomeyPro connectivity and network settings",
            "timestamp": time.time(),
            "details": str(e)
        })
    except TimeoutError as e:
        logger.error(f"Device registry resource timeout: {e}")
        return str({
            "error": "Failed to retrieve device registry due to timeout",
            "error_type": "timeout",
            "fallback_available": False,
            "suggested_action": "HomeyPro may be overloaded, try again in a few moments",
            "timestamp": time.time(),
            "details": str(e)
        })
    except Exception as e:
        logger.error(f"Device registry resource unexpected error: {type(e).__name__}: {e}")
        return str({
            "error": "Failed to retrieve device registry due to unexpected error",
            "error_type": "unknown",
            "fallback_available": False,
            "suggested_action": "Check system logs and HomeyPro status",
            "timestamp": time.time(),
            "details": f"{type(e).__name__}: {str(e)}"
        })


@mcp.resource("homey://zones/hierarchy")
async def zone_hierarchy_resource() -> str:
    """
    Provides zone structure with device associations, including zone relationships 
    and device assignments.
    
    Returns:
        JSON string containing zone hierarchy data
    """
    async def fetch_zone_hierarchy():
        try:
            client = await ensure_client()
            
            # Fetch zones and devices
            zones = await client.zones.get_zones()
            devices = await client.devices.get_devices()
            
            # Create device lookup by zone
            devices_by_zone = {}
            for device in devices:
                zone_id = getattr(device, 'zone', None)
                if zone_id:
                    if zone_id not in devices_by_zone:
                        devices_by_zone[zone_id] = []
                    devices_by_zone[zone_id].append({
                        "id": getattr(device, 'id', 'unknown'),
                        "name": getattr(device, 'name', 'Unknown Device'),
                        "class": getattr(device, 'class_', 'unknown'),
                        "available": getattr(device, 'available', False)
                    })
            
            zone_hierarchy = {
                "zones": [],
                "summary": {
                    "total_zones": len(zones),
                    "zones_with_devices": 0,
                    "total_devices_assigned": 0,
                    "zone_types": set()
                },
                "timestamp": time.time(),
                "cache_info": {
                    "ttl_seconds": 300,  # 5 minutes for zone configuration
                    "data_type": "zone_hierarchy"
                }
            }
            
            # Process each zone
            for zone in zones:
                zone_id = getattr(zone, 'id', 'unknown')
                zone_info = {
                    "id": zone_id,
                    "name": getattr(zone, 'name', 'Unknown Zone'),
                    "parent": getattr(zone, 'parent', None),
                    "active": getattr(zone, 'active', True),
                    "icon": getattr(zone, 'icon', None),
                    "devices": devices_by_zone.get(zone_id, []),
                    "device_count": len(devices_by_zone.get(zone_id, [])),
                    "online_device_count": len([d for d in devices_by_zone.get(zone_id, []) if d["available"]])
                }
                
                # Track statistics
                if zone_info["device_count"] > 0:
                    zone_hierarchy["summary"]["zones_with_devices"] += 1
                    zone_hierarchy["summary"]["total_devices_assigned"] += zone_info["device_count"]
                
                # Track zone types (based on icon or name patterns)
                zone_type = "general"
                if zone_info["icon"]:
                    zone_type = zone_info["icon"]
                elif any(keyword in zone_info["name"].lower() for keyword in ["bedroom", "living", "kitchen", "bathroom"]):
                    zone_type = "room"
                elif any(keyword in zone_info["name"].lower() for keyword in ["outdoor", "garden", "garage"]):
                    zone_type = "outdoor"
                
                zone_hierarchy["summary"]["zone_types"].add(zone_type)
                zone_info["type"] = zone_type
                
                zone_hierarchy["zones"].append(zone_info)
            
            # Build parent-child relationships
            zone_lookup = {zone["id"]: zone for zone in zone_hierarchy["zones"]}
            for zone in zone_hierarchy["zones"]:
                if zone["parent"] and zone["parent"] in zone_lookup:
                    parent_zone = zone_lookup[zone["parent"]]
                    if "children" not in parent_zone:
                        parent_zone["children"] = []
                    parent_zone["children"].append(zone["id"])
            
            # Convert sets to lists for JSON serialization
            zone_hierarchy["summary"]["zone_types"] = list(zone_hierarchy["summary"]["zone_types"])
            
            logger.info(f"Zone hierarchy generated: {len(zones)} zones, "
                       f"{zone_hierarchy['summary']['zones_with_devices']} with devices")
            return zone_hierarchy
            
        except Exception as e:
            logger.error(f"Failed to fetch zone hierarchy: {e}")
            raise
    
    try:
        # Use 5-minute TTL for zone configuration data
        data = await _resource_cache.get_or_fetch("zone_hierarchy", fetch_zone_hierarchy, 300)
        
        # Handle stale data response
        if isinstance(data, dict) and "is_stale" in data:
            stale_data = data["data"]
            stale_data["cache_info"]["is_stale"] = True
            stale_data["cache_info"]["stale_reason"] = "HomeyPro unreachable, using cached data"
            stale_data["cache_info"]["error_type"] = data.get("error_type", "unknown")
            logger.info(f"Returning stale zone hierarchy data due to {data.get('error_type', 'unknown')} error")
            return str(stale_data)
        
        logger.debug("Successfully retrieved fresh zone hierarchy data")
        return str(data)
        
    except ConnectionError as e:
        logger.error(f"Zone hierarchy resource connection failed: {e}")
        return str({
            "error": "Failed to retrieve zone hierarchy due to connection issues",
            "error_type": "connection",
            "fallback_available": False,
            "suggested_action": "Check HomeyPro connectivity and network settings",
            "timestamp": time.time(),
            "details": str(e)
        })
    except TimeoutError as e:
        logger.error(f"Zone hierarchy resource timeout: {e}")
        return str({
            "error": "Failed to retrieve zone hierarchy due to timeout",
            "error_type": "timeout",
            "fallback_available": False,
            "suggested_action": "HomeyPro may be overloaded, try again in a few moments",
            "timestamp": time.time(),
            "details": str(e)
        })
    except Exception as e:
        logger.error(f"Zone hierarchy resource unexpected error: {type(e).__name__}: {e}")
        return str({
            "error": "Failed to retrieve zone hierarchy due to unexpected error",
            "error_type": "unknown",
            "fallback_available": False,
            "suggested_action": "Check system logs and HomeyPro status",
            "timestamp": time.time(),
            "details": f"{type(e).__name__}: {str(e)}"
        })


@mcp.resource("homey://flows/catalog")
async def flow_catalog_resource() -> str:
    """
    Provides available flows with metadata, status, and execution statistics.
    Includes flow types, enabled/disabled status, and basic execution info.
    
    Returns:
        JSON string containing flow catalog data
    """
    async def fetch_flow_catalog():
        try:
            client = await ensure_client()
            
            # Fetch all flows
            flows = await client.flows.get_flows()
            
            flow_catalog = {
                "flows": [],
                "summary": {
                    "total_count": len(flows),
                    "enabled_count": 0,
                    "disabled_count": 0,
                    "flow_types": set(),
                    "trigger_types": set()
                },
                "timestamp": time.time(),
                "cache_info": {
                    "ttl_seconds": 120,  # 2 minutes for flow information
                    "data_type": "flow_catalog"
                }
            }
            
            # Process each flow
            for flow in flows:
                flow_info = {
                    "id": getattr(flow, 'id', 'unknown'),
                    "name": getattr(flow, 'name', 'Unknown Flow'),
                    "enabled": getattr(flow, 'enabled', False),
                    "folder": getattr(flow, 'folder', None),
                    "type": getattr(flow, 'type', 'unknown'),
                    "trigger": {},
                    "conditions": [],
                    "actions": [],
                    "broken": getattr(flow, 'broken', False),
                    "last_executed": getattr(flow, 'lastExecuted', None)
                }
                
                # Track enabled/disabled status
                if flow_info["enabled"]:
                    flow_catalog["summary"]["enabled_count"] += 1
                else:
                    flow_catalog["summary"]["disabled_count"] += 1
                
                # Track flow types
                if flow_info["type"]:
                    flow_catalog["summary"]["flow_types"].add(flow_info["type"])
                
                # Process trigger information
                if hasattr(flow, 'trigger') and flow.trigger:
                    trigger = flow.trigger
                    flow_info["trigger"] = {
                        "id": getattr(trigger, 'id', 'unknown'),
                        "uri": getattr(trigger, 'uri', 'unknown'),
                        "title": getattr(trigger, 'title', 'Unknown Trigger')
                    }
                    
                    # Extract trigger type from URI
                    trigger_uri = flow_info["trigger"]["uri"]
                    if trigger_uri and trigger_uri != 'unknown':
                        trigger_type = trigger_uri.split(':')[0] if ':' in trigger_uri else 'unknown'
                        flow_catalog["summary"]["trigger_types"].add(trigger_type)
                
                # Process conditions (simplified)
                if hasattr(flow, 'conditions') and flow.conditions:
                    for condition in flow.conditions:
                        condition_info = {
                            "id": getattr(condition, 'id', 'unknown'),
                            "uri": getattr(condition, 'uri', 'unknown'),
                            "title": getattr(condition, 'title', 'Unknown Condition')
                        }
                        flow_info["conditions"].append(condition_info)
                
                # Process actions (simplified)
                if hasattr(flow, 'actions') and flow.actions:
                    for action in flow.actions:
                        action_info = {
                            "id": getattr(action, 'id', 'unknown'),
                            "uri": getattr(action, 'uri', 'unknown'),
                            "title": getattr(action, 'title', 'Unknown Action')
                        }
                        flow_info["actions"].append(action_info)
                
                # Add execution statistics if available
                flow_info["statistics"] = {
                    "condition_count": len(flow_info["conditions"]),
                    "action_count": len(flow_info["actions"]),
                    "has_trigger": bool(flow_info["trigger"].get("id")),
                    "is_broken": flow_info["broken"]
                }
                
                flow_catalog["flows"].append(flow_info)
            
            # Convert sets to lists for JSON serialization
            flow_catalog["summary"]["flow_types"] = list(flow_catalog["summary"]["flow_types"])
            flow_catalog["summary"]["trigger_types"] = list(flow_catalog["summary"]["trigger_types"])
            
            logger.info(f"Flow catalog generated: {len(flows)} flows, "
                       f"{flow_catalog['summary']['enabled_count']} enabled")
            return flow_catalog
            
        except Exception as e:
            logger.error(f"Failed to fetch flow catalog: {e}")
            raise
    
    try:
        # Use 2-minute TTL for flow information
        data = await _resource_cache.get_or_fetch("flow_catalog", fetch_flow_catalog, 120)
        
        # Handle stale data response
        if isinstance(data, dict) and "is_stale" in data:
            stale_data = data["data"]
            stale_data["cache_info"]["is_stale"] = True
            stale_data["cache_info"]["stale_reason"] = "HomeyPro unreachable, using cached data"
            stale_data["cache_info"]["error_type"] = data.get("error_type", "unknown")
            logger.info(f"Returning stale flow catalog data due to {data.get('error_type', 'unknown')} error")
            return str(stale_data)
        
        logger.debug("Successfully retrieved fresh flow catalog data")
        return str(data)
        
    except ConnectionError as e:
        logger.error(f"Flow catalog resource connection failed: {e}")
        return str({
            "error": "Failed to retrieve flow catalog due to connection issues",
            "error_type": "connection",
            "fallback_available": False,
            "suggested_action": "Check HomeyPro connectivity and network settings",
            "timestamp": time.time(),
            "details": str(e)
        })
    except TimeoutError as e:
        logger.error(f"Flow catalog resource timeout: {e}")
        return str({
            "error": "Failed to retrieve flow catalog due to timeout",
            "error_type": "timeout",
            "fallback_available": False,
            "suggested_action": "HomeyPro may be overloaded, try again in a few moments",
            "timestamp": time.time(),
            "details": str(e)
        })
    except Exception as e:
        logger.error(f"Flow catalog resource unexpected error: {type(e).__name__}: {e}")
        return str({
            "error": "Failed to retrieve flow catalog due to unexpected error",
            "error_type": "unknown",
            "fallback_available": False,
            "suggested_action": "Check system logs and HomeyPro status",
            "timestamp": time.time(),
            "details": f"{type(e).__name__}: {str(e)}"
        })