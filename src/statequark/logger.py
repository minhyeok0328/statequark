"""
Logging system for StateQuark.

This module provides a comprehensive logging system for debugging and monitoring
StateQuark operations in IoT and embedded systems.
"""

import logging
import sys
from typing import Optional

# Create logger instance
_logger: Optional[logging.Logger] = None
_debug_enabled: bool = False


def get_logger() -> logging.Logger:
    """
    Get or create the StateQuark logger instance.

    Returns:
        logging.Logger: The configured logger instance.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger("statequark")
        _logger.setLevel(logging.WARNING)
        _logger.propagate = False

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter(
            (
                "[%(asctime)s] %(levelname)s "
                "[%(name)s.%(funcName)s:%(lineno)d] %(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        # Add handler if not already added
        if not _logger.handlers:
            _logger.addHandler(handler)

    return _logger


def enable_debug() -> None:
    """
    Enable debug logging for StateQuark.

    When debug mode is enabled, detailed logs will be output including:
    - Quark creation and initialization
    - Value changes
    - Callback executions
    - Thread pool operations
    - Dependency tracking
    """
    global _debug_enabled
    _debug_enabled = True
    logger = get_logger()
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug logging enabled for StateQuark")


def disable_debug() -> None:
    """
    Disable debug logging for StateQuark.

    Returns logging level to WARNING (default).
    """
    global _debug_enabled
    _debug_enabled = False
    logger = get_logger()
    logger.setLevel(logging.WARNING)


def is_debug_enabled() -> bool:
    """
    Check if debug logging is currently enabled.

    Returns:
        bool: True if debug logging is enabled, False otherwise.
    """
    return _debug_enabled


def log_debug(message: str, *args: object) -> None:
    """
    Log a debug message if debug mode is enabled.

    Args:
        message: The log message format string.
        *args: Arguments to format into the message.
    """
    if _debug_enabled:
        get_logger().debug(message, *args)


def log_info(message: str, *args: object) -> None:
    """
    Log an info message.

    Args:
        message: The log message format string.
        *args: Arguments to format into the message.
    """
    get_logger().info(message, *args)


def log_warning(message: str, *args: object) -> None:
    """
    Log a warning message.

    Args:
        message: The log message format string.
        *args: Arguments to format into the message.
    """
    get_logger().warning(message, *args)


def log_error(message: str, *args: object) -> None:
    """
    Log an error message.

    Args:
        message: The log message format string.
        *args: Arguments to format into the message.
    """
    get_logger().error(message, *args)
