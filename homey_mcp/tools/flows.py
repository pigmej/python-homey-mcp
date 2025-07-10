"""Flow-related tools for HomeyPro MCP Server."""

from typing import Any, Dict, Optional

from ..client.manager import ensure_client
from ..utils.logging import get_logger
from ..utils.pagination import paginate_results, parse_cursor, PaginationError
from ..mcp_instance import mcp

logger = get_logger(__name__)


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