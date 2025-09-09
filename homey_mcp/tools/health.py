"""Health check and monitoring tools for HomeyPro MCP Server."""

import time
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass

from ..client.manager import ensure_client
from ..config import get_config
from ..utils.logging import get_logger
from ..mcp_instance import mcp

logger = get_logger(__name__)


@dataclass
class HealthStatus:
    """Health status information."""
    
    is_healthy: bool
    timestamp: datetime
    response_time_ms: float
    homey_reachable: bool
    homey_version: Optional[str] = None
    device_count: Optional[int] = None
    errors: Optional[list] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "is_healthy": self.is_healthy,
            "timestamp": self.timestamp.isoformat(),
            "response_time_ms": self.response_time_ms,
            "homey_reachable": self.homey_reachable,
            "homey_version": self.homey_version,
            "device_count": self.device_count,
            "errors": self.errors or [],
        }


# Global health status cache
_last_health_check: Optional[HealthStatus] = None
_health_check_interval = 30  # seconds


async def perform_health_check(force: bool = False) -> HealthStatus:
    """Perform a comprehensive health check.
    
    Args:
        force: Force a new health check even if recent data exists
        
    Returns:
        HealthStatus object with current system status
    """
    global _last_health_check
    
    # Return cached result if recent and not forced
    if (
        not force 
        and _last_health_check 
        and (datetime.now() - _last_health_check.timestamp).seconds < _health_check_interval
    ):
        logger.debug("Returning cached health status")
        return _last_health_check
    
    logger.info("Performing health check")
    start_time = time.time()
    errors = []
    
    # Initialize status
    status = HealthStatus(
        is_healthy=True,
        timestamp=datetime.now(),
        response_time_ms=0.0,
        homey_reachable=False,
    )
    
    try:
        # Test connection to HomeyPro
        client = await ensure_client()
        
        # Try to get basic system info
        try:
            devices = await client.devices.get_devices()
            status.device_count = len(devices)
            status.homey_reachable = True
            logger.debug(f"Health check found {len(devices)} devices")
        except Exception as e:
            errors.append(f"Failed to get device count: {str(e)}")
            status.homey_reachable = False
        
        # Try to get system version if available
        try:
            system_info = await client.system.get_system_config()
            if hasattr(system_info, 'version'):
                status.homey_version = system_info.version
        except Exception as e:
            errors.append(f"Failed to get system version: {str(e)}")
        
    except Exception as e:
        logger.warning(f"Health check connection failed: {e}")
        errors.append(f"Connection failed: {str(e)}")
        status.homey_reachable = False
        status.is_healthy = False
    
    # Calculate response time
    status.response_time_ms = (time.time() - start_time) * 1000
    
    # Set overall health status
    if errors:
        status.errors = errors
        if not status.homey_reachable:
            status.is_healthy = False
    
    # Cache the result
    _last_health_check = status
    
    logger.info(
        f"Health check completed: healthy={status.is_healthy}, "
        f"reachable={status.homey_reachable}, response_time={status.response_time_ms:.1f}ms"
    )
    
    return status


@mcp.tool()
async def health_check(detailed: bool = False) -> Dict[str, Any]:
    """
    Perform a health check of the HomeyPro MCP Server.
    
    This tool checks connectivity to HomeyPro, response times, and basic
    system functionality. Useful for monitoring and diagnostics.
    
    Args:
        detailed: Whether to include detailed diagnostic information
        
    Returns:
        Health status information including connectivity and performance metrics
    """
    try:
        status = await perform_health_check()
        result = status.to_dict()
        
        if detailed:
            config = get_config()
            result["config"] = {
                "api_url": config.api_url,
                "timeout": config.timeout,
                "verify_ssl": config.verify_ssl,
                "cache_ttl": config.cache_ttl,
            }
            result["server_info"] = {
                "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
                "uptime_seconds": time.time() - start_time if 'start_time' in globals() else 0,
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "is_healthy": False,
            "timestamp": datetime.now().isoformat(),
            "error": f"Health check failed: {str(e)}",
            "error_type": "health_check_failure",
        }


@mcp.tool()
async def get_metrics() -> Dict[str, Any]:
    """
    Get performance and usage metrics for the HomeyPro MCP Server.
    
    Returns:
        Dictionary containing various performance metrics and statistics
    """
    try:
        status = await perform_health_check()
        
        # Get basic metrics
        metrics = {
            "health": {
                "is_healthy": status.is_healthy,
                "response_time_ms": status.response_time_ms,
                "homey_reachable": status.homey_reachable,
                "last_check": status.timestamp.isoformat(),
            },
            "system": {
                "device_count": status.device_count,
                "homey_version": status.homey_version,
            },
            "timestamp": datetime.now().isoformat(),
        }
        
        # Add error information if present
        if status.errors:
            metrics["errors"] = status.errors
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return {
            "error": f"Failed to get metrics: {str(e)}",
            "error_type": "metrics_failure",
            "timestamp": datetime.now().isoformat(),
        }


# Module initialization - record start time
start_time = time.time()
