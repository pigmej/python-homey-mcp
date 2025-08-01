"""Test configuration for HomeyPro MCP Server."""

from .config import HomeyConfig


def get_test_config() -> HomeyConfig:
    """Get a test configuration with safe defaults."""
    return HomeyConfig(
        api_url="http://test.local",
        api_token="test_token_12345678901234567890",
        timeout=30.0,
        verify_ssl=False,
        cache_ttl=300,
        max_page_size=100,
        default_page_size=25,
        log_level="DEBUG",
    )
