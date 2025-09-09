"""Flow-related tools for HomeyPro MCP Server."""

from operator import attrgetter

from typing import Any, Dict, Optional
from typing_extensions import Annotated
from pydantic.fields import Field

from ..client.manager import ensure_client
from ..utils.logging import get_logger
from ..utils.pagination import paginate_results, parse_cursor, PaginationError
from ..mcp_instance import mcp

logger = get_logger(__name__)


async def detect_flow_type(flow_id: str) -> Optional[str]:
    """
    Detect the type of a flow by checking if it exists in normal or advanced flows.

    This utility function is used by the consolidated flow functions to determine
    whether a flow_id belongs to a normal or advanced flow. It first checks if the
    flow exists in the normal flows list, and if not, checks the advanced flows list.

    The function implements graceful error handling to continue checking advanced flows
    even if the normal flows API fails, and vice versa. This ensures maximum resilience
    when determining flow types.

    Args:
        flow_id: The unique identifier of the flow to check

    Returns:
        "normal" if found in normal flows, "advanced" if found in advanced flows,
        None if not found in either type

    Raises:
        Exception: If there's an error accessing both flow APIs
    """
    try:
        client = await ensure_client()

        # First check normal flows
        try:
            normal_flows = await client.flows.get_flows()
            for flow in normal_flows:
                if flow.id == flow_id:
                    return "normal"
        except Exception as e:
            logger.warning(f"Error checking normal flows for flow_id {flow_id}: {e}")
            # Continue to check advanced flows even if normal flows fail

        # Then check advanced flows
        try:
            advanced_flows = await client.flows.get_advanced_flows()
            for flow in advanced_flows:
                if flow.id == flow_id:
                    return "advanced"
        except Exception as e:
            logger.warning(f"Error checking advanced flows for flow_id {flow_id}: {e}")
            # If both APIs fail, we should raise an exception
            raise Exception(f"Failed to check both normal and advanced flows: {e}")

        # Flow not found in either type
        return None

    except Exception as e:
        error_msg = f"Error detecting flow type for flow_id {flow_id}: {e}"
        logger.error(error_msg)
        raise Exception(error_msg) from e


async def _list_flows_impl(
    cursor: Optional[str] = None,
    compact: Annotated[
        bool,
        Field(
            description="Optional switch for compact results, by default true. Switch only if really needed"
        ),
    ] = True,
) -> Dict[str, Any]:
    """
    Implementation of list_flows functionality.

    This function retrieves both normal and advanced flows, combines them into a single
    list, and applies pagination to the combined results. Each flow is tagged with a
    "flow_type" field indicating whether it is a "normal" or "advanced" flow.

    The function implements graceful error handling to continue with partial results
    if one of the flow APIs fails. Only if both APIs fail will it return an error.

    Args:
        cursor: Optional cursor for pagination. If provided, should be a cursor
               returned from a previous call to this function.
        compact: Optional switch for compact results, by default true. Switch only if really needed


    Returns:
        Paginated list of flows with flow_type field indicating "normal" or "advanced".
    """
    try:
        cursor_params = parse_cursor(cursor)
        client = await ensure_client()
        combined_flows = []
        normal_flows_error = None
        advanced_flows_error = None

        # Set up dumper based on compact flag
        if compact:
            dumper = attrgetter("model_dump_compact")
        else:
            dumper = attrgetter("model_dump")

        # Get normal flows
        try:
            normal_flows = await client.flows.get_flows()
            # Add flow_type field and convert to dictionaries
            normal_flow_dicts = []
            for flow in normal_flows:
                flow_dict = dumper(flow)()
                flow_dict["flow_type"] = "normal"
                normal_flow_dicts.append(flow_dict)
            combined_flows.extend(normal_flow_dicts)
        except Exception as e:
            normal_flows_error = str(e)
            logger.warning(f"Error fetching normal flows: {e}")
            # Continue to fetch advanced flows even if normal flows fail

        # Get advanced flows
        try:
            advanced_flows = await client.flows.get_advanced_flows()
            # Add flow_type field and convert to dictionaries
            advanced_flow_dicts = []
            for flow in advanced_flows:
                flow_dict = dumper(flow)()
                flow_dict["flow_type"] = "advanced"
                advanced_flow_dicts.append(flow_dict)
            combined_flows.extend(advanced_flow_dicts)
        except Exception as e:
            advanced_flows_error = str(e)
            logger.warning(f"Error fetching advanced flows: {e}")
            # Continue with normal flows if advanced flows fail

        # If both APIs failed, return error
        if normal_flows_error and advanced_flows_error:
            error_msg = f"Failed to fetch both normal and advanced flows: {normal_flows_error}, {advanced_flows_error}"
            logger.error(error_msg)
            return {"error": error_msg}

        # Apply pagination to combined results
        result = paginate_results(combined_flows, cursor_params)

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
async def list_flows(
    cursor: Optional[str] = None,
    compact: Annotated[
        bool,
        Field(
            description="Optional switch for compact results, by default true. Switch only if really needed"
        ),
    ] = True,
) -> Dict[str, Any]:
    """
    List all flows (both normal and advanced) with pagination support.

    This consolidated function retrieves both normal and advanced flows in a single call,
    combining them into a unified response. Each flow includes a "flow_type" field
    indicating whether it is a "normal" or "advanced" flow.

    Pagination works seamlessly across the combined result set, allowing you to
    navigate through all flows regardless of type.

    Args:
        cursor: Optional cursor for pagination. If provided, should be a cursor
               returned from a previous call to this function.
        compact: Optional switch for compact results, by default true. Switch only if really needed


    Returns:
        Dict with the following structure:
        {
            "flows": [
                {
                    "id": "flow_id",
                    "name": "Flow Name",
                    "enabled": true,
                    "flow_type": "normal" | "advanced",
                    ... (other flow properties)
                },
                ...
            ],
            "pagination": {
                "total_count": int,
                "page_size": int,
                "offset": int,
                "has_next": bool,
                "next_cursor": str | None
            }
        }

        If an error occurs, returns:
        {
            "error": "Error message"
        }
    """
    return await _list_flows_impl(cursor, compact)


async def _trigger_flow_impl(flow_id: str) -> Dict[str, Any]:
    """
    Implementation of trigger_flow functionality.

    This function first detects the type of flow (normal or advanced) using the
    detect_flow_type utility function, then triggers the appropriate API based on
    the detected type. It includes comprehensive error handling for various scenarios:

    1. Flow not found in either normal or advanced flows
    2. Flow trigger fails
    3. Flow type detection fails
    4. API connection errors

    The response includes a "flow_type" field indicating whether the triggered flow
    was a "normal" or "advanced" flow, providing consistent response structures
    regardless of the underlying flow type.

    Args:
        flow_id: The unique identifier of the flow to trigger.

    Returns:
        Success status and flow information with flow_type included.
    """
    try:
        client = await ensure_client()

        # First detect the flow type
        flow_type = await detect_flow_type(flow_id)

        if flow_type is None:
            return {
                "success": False,
                "error": f"Flow not found: {flow_id}",
                "flow_id": flow_id,
            }

        # Trigger the appropriate flow type
        if flow_type == "normal":
            success = await client.flows.trigger_flow(flow_id)
            if success:
                # Get flow details
                flow = await client.flows.get_flow(flow_id)
                return {
                    "success": True,
                    "flow_id": flow_id,
                    "flow_name": flow.name,
                    "flow_type": "normal",
                }
        else:  # flow_type == "advanced"
            success = await client.flows.trigger_advanced_flow(flow_id)
            if success:
                # Get flow details
                flow = await client.flows.get_advanced_flow(flow_id)
                return {
                    "success": True,
                    "flow_id": flow_id,
                    "flow_name": flow.name,
                    "flow_type": "advanced",
                }

        # If we get here, the trigger failed
        return {
            "success": False,
            "error": f"Failed to trigger {flow_type} flow",
            "flow_id": flow_id,
            "flow_type": flow_type,
        }

    except Exception as e:
        logger.error(f"Error triggering flow {flow_id}: {e}")
        return {"error": f"Failed to trigger flow: {e}"}


@mcp.tool()
async def trigger_flow(flow_id: str) -> Dict[str, Any]:
    """
    Trigger a flow (automatically detects normal vs advanced).

    This consolidated function automatically detects whether the provided flow_id
    belongs to a normal or advanced flow, and triggers it using the appropriate API.
    The detection is done by checking if the flow exists in either the normal or
    advanced flows list.

    The response includes a "flow_type" field indicating whether the triggered flow
    was a "normal" or "advanced" flow.

    Args:
        flow_id: The unique identifier of the flow to trigger.

    Returns:
        Dict with the following structure on success:
        {
            "success": true,
            "flow_id": "flow_id",
            "flow_name": "Flow Name",
            "flow_type": "normal" | "advanced"
        }

        Dict with the following structure on failure:
        {
            "success": false,
            "error": "Error message",
            "flow_id": "flow_id",
            "flow_type": "normal" | "advanced"  # Only included if flow type was detected
        }

        If the flow is not found or an error occurs:
        {
            "success": false,
            "error": "Flow not found: flow_id",
            "flow_id": "flow_id"
        }
        or
        {
            "error": "Error message"
        }
    """
    return await _trigger_flow_impl(flow_id)


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

    Note: This function only returns normal flows in the specified folder.
    To get both normal and advanced flows, use list_flows() and filter by folder.

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

    Note: This function only returns normal flows without a folder.
    To get both normal and advanced flows without a folder, use list_flows()
    and filter by folder status.

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
