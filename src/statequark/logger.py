"""Logging system for StateQuark."""

import logging
import sys
from typing import Optional

_logger: Optional[logging.Logger] = None
_debug_enabled: bool = False


def get_logger() -> logging.Logger:
    """Get or create the StateQuark logger instance."""
    global _logger
    if _logger is None:
        _logger = logging.getLogger("statequark")
        _logger.setLevel(logging.WARNING)
        _logger.propagate = False

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s",
                datefmt="%H:%M:%S",
            )
        )

        if not _logger.handlers:
            _logger.addHandler(handler)

    return _logger


def enable_debug() -> None:
    """Enable debug logging."""
    global _debug_enabled
    _debug_enabled = True
    get_logger().setLevel(logging.DEBUG)


def disable_debug() -> None:
    """Disable debug logging."""
    global _debug_enabled
    _debug_enabled = False
    get_logger().setLevel(logging.WARNING)


def is_debug_enabled() -> bool:
    """Check if debug logging is enabled."""
    return _debug_enabled


def log_debug(message: str, *args: object) -> None:
    """Log debug message (only if debug enabled)."""
    if _debug_enabled:
        get_logger().debug(message, *args)


def log_info(message: str, *args: object) -> None:
    """Log info message."""
    get_logger().info(message, *args)


def log_warning(message: str, *args: object) -> None:
    """Log warning message."""
    get_logger().warning(message, *args)


def log_error(message: str, *args: object) -> None:
    """Log error message."""
    get_logger().error(message, *args)
