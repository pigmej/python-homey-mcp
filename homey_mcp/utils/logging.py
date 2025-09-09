"""Logging utilities for HomeyPro MCP Server."""

import logging

from ..config import get_config

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    # Configure logging if not already configured
    if not logging.getLogger().handlers:
        config = get_config()
        logging.basicConfig(level=config.log_level)
    
    return logging.getLogger(name)