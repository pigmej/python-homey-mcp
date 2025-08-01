"""Custom exceptions for HomeyPro MCP Server."""


class HomeyConnectionError(ConnectionError):
    """Raised when connection to Homey fails."""
    pass


class HomeyTimeoutError(TimeoutError):
    """Raised when Homey request times out."""
    pass