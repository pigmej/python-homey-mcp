"""Pagination utilities for HomeyPro MCP Server."""

import json
from typing import Any, Dict, List, Optional

from ..config import get_config


class PaginationError(Exception):
    """Raised when pagination parameters are invalid."""

    pass


def parse_cursor(cursor: Optional[str]) -> Dict[str, Any]:
    """Parse cursor string into pagination parameters."""
    config = get_config()
    
    if not cursor or cursor == "null":
        return {"offset": 0, "page_size": config.default_page_size}

    try:
        data = json.loads(cursor)
        if not isinstance(data, dict):
            raise ValueError("Cursor must be a JSON object")

        offset = data.get("offset", 0)
        page_size = data.get("page_size", config.default_page_size)

        if not isinstance(offset, int) or offset < 0:
            raise ValueError("Offset must be a non-negative integer")
        if (
            not isinstance(page_size, int)
            or page_size <= 0
            or page_size > config.max_page_size
        ):
            raise ValueError(f"Page size must be between 1 and {config.max_page_size}")

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
