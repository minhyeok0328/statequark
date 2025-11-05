"""
Configuration management for StateQuark.

This module provides centralized configuration management for the StateQuark library,
optimized for IoT and embedded systems with limited resources.
"""

from dataclasses import dataclass, field
from typing import Optional

from .logger import disable_debug as _disable_debug
from .logger import enable_debug as _enable_debug


@dataclass
class StateQuarkConfig:
    """
    Configuration for StateQuark library.

    This dataclass holds all configuration options for StateQuark,
    following best practices for embedded systems.

    Attributes:
        debug: Enable debug logging for detailed operation tracking.
        max_workers: Maximum number of worker threads in the shared pool.
                    Lower values conserve resources on embedded systems.
        thread_name_prefix: Prefix for thread names to aid in debugging.
        auto_cleanup: Automatically cleanup resources on application exit.
    """

    debug: bool = False
    max_workers: int = 4
    thread_name_prefix: str = "quark-callback"
    auto_cleanup: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        if self.max_workers > 32:
            raise ValueError("max_workers should not exceed 32 for embedded systems")

        # Apply debug setting
        if self.debug:
            _enable_debug()
        else:
            _disable_debug()


# Global configuration instance
_config: Optional[StateQuarkConfig] = None


def get_config() -> StateQuarkConfig:
    """
    Get the global StateQuark configuration.

    Returns:
        StateQuarkConfig: The current configuration instance.
    """
    global _config
    if _config is None:
        _config = StateQuarkConfig()
    return _config


def set_config(config: StateQuarkConfig) -> None:
    """
    Set the global StateQuark configuration.

    Args:
        config: The new configuration to use.

    Example:
        >>> from statequark import StateQuarkConfig, set_config
        >>> config = StateQuarkConfig(debug=True, max_workers=2)
        >>> set_config(config)
    """
    global _config
    _config = config

    # Apply debug setting
    if config.debug:
        _enable_debug()
    else:
        _disable_debug()


def enable_debug() -> None:
    """
    Enable debug mode in the current configuration.

    This is a convenience function that modifies the global configuration
    to enable debug logging.

    Example:
        >>> from statequark import enable_debug
        >>> enable_debug()
    """
    config = get_config()
    config.debug = True
    _enable_debug()


def disable_debug() -> None:
    """
    Disable debug mode in the current configuration.

    Example:
        >>> from statequark import disable_debug
        >>> disable_debug()
    """
    config = get_config()
    config.debug = False
    _disable_debug()


def reset_config() -> None:
    """
    Reset configuration to default values.

    This is useful for testing or when you want to restore default behavior.
    """
    global _config
    _config = StateQuarkConfig()
