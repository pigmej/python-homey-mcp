"""Custom exceptions for HomeyPro MCP Server."""

from typing import Any, Dict, Optional


class HomeyMCPError(Exception):
    """Base exception for HomeyPro MCP Server errors."""

    def __init__(
        self,
        message: str,
        error_type: str = "unknown",
        suggested_action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_type = error_type
        self.suggested_action = suggested_action
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        result = {
            "error": self.message,
            "error_type": self.error_type,
        }

        if self.suggested_action:
            result["suggested_action"] = self.suggested_action

        if self.details:
            result["details"] = self.details

        return result


class HomeyConnectionError(HomeyMCPError):
    """Raised when connection to HomeyPro fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_type="connection",
            suggested_action="Check HomeyPro connectivity and network settings",
            details=details,
        )


class HomeyTimeoutError(HomeyMCPError):
    """Raised when requests to HomeyPro timeout."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_type="timeout",
            suggested_action="HomeyPro may be overloaded, try again in a few moments",
            details=details,
        )


class HomeyAuthenticationError(HomeyMCPError):
    """Raised when authentication with HomeyPro fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_type="authentication",
            suggested_action="Check your HOMEY_API_TOKEN and ensure it's valid",
            details=details,
        )


class HomeyNotFoundError(HomeyMCPError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"{resource_type.title()} with ID '{resource_id}' not found"
        super().__init__(
            message=message,
            error_type="not_found",
            suggested_action=f"Verify the {resource_type} ID and try again",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                **(details or {}),
            },
        )


class HomeyValidationError(HomeyMCPError):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_type="validation",
            suggested_action="Check request parameters and try again",
            details={"field": field, **(details or {})} if field else details,
        )


class HomeyCacheError(HomeyMCPError):
    """Raised when cache operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_type="cache",
            suggested_action="Cache issue, data may be stale or unavailable",
            details=details,
        )
