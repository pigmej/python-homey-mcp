"""Configuration management for HomeyPro MCP Server."""

import os
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


@dataclass
class HomeyConfig:
    """Configuration settings for HomeyPro MCP Server."""

    api_url: str
    api_token: str
    timeout: float = 30.0
    verify_ssl: bool = False
    cache_ttl: int = 300  # 5 minutes default
    max_page_size: int = 100
    default_page_size: int = 50
    log_level: str = "INFO"

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_url()
        self._validate_token()

    def _validate_url(self):
        """Validate API URL format."""
        parsed = urlparse(self.api_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(
                f"Invalid API URL format: {self.api_url}. "
                "Expected format: http://192.168.1.100"
            )

    def _validate_token(self):
        """Validate API token is present."""
        if not self.api_token or len(self.api_token.strip()) < 10:
            raise ValueError(
                "API token must be provided and at least 10 characters long"
            )

    @classmethod
    def from_env(cls) -> "HomeyConfig":
        """Create configuration from environment variables."""
        api_url = os.getenv("HOMEY_API_URL")
        api_token = os.getenv("HOMEY_API_TOKEN")

        if not api_url:
            raise ValueError("HOMEY_API_URL environment variable is required")
        if not api_token:
            raise ValueError("HOMEY_API_TOKEN environment variable is required")

        return cls(
            api_url=api_url,
            api_token=api_token,
            timeout=float(os.getenv("HOMEY_TIMEOUT", "30.0")),
            verify_ssl=os.getenv("HOMEY_VERIFY_SSL", "false").lower() == "true",
            cache_ttl=int(os.getenv("HOMEY_CACHE_TTL", "300")),
            max_page_size=int(os.getenv("HOMEY_MAX_PAGE_SIZE", "100")),
            default_page_size=int(os.getenv("HOMEY_DEFAULT_PAGE_SIZE", "25")),
            log_level=os.getenv("HOMEY_LOG_LEVEL", "INFO").upper(),
        )


# Global configuration instance
_config: Optional[HomeyConfig] = None


def get_config() -> HomeyConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = HomeyConfig.from_env()
    return _config


def set_config(config: HomeyConfig) -> None:
    """Set the global configuration instance (mainly for testing)."""
    global _config
    _config = config
