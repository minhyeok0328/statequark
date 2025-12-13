"""Configuration management for StateQuark."""

from dataclasses import dataclass
from typing import Optional

from .logger import disable_debug as _disable_debug
from .logger import enable_debug as _enable_debug


@dataclass
class StateQuarkConfig:
    """Configuration for StateQuark library."""

    debug: bool = False
    max_workers: int = 4
    thread_name_prefix: str = "quark-callback"
    auto_cleanup: bool = True

    def __post_init__(self) -> None:
        if self.max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        if self.max_workers > 32:
            raise ValueError("max_workers should not exceed 32 for embedded systems")

        if self.debug:
            _enable_debug()
        else:
            _disable_debug()


_config: Optional[StateQuarkConfig] = None


def get_config() -> StateQuarkConfig:
    """Get the global configuration."""
    global _config
    if _config is None:
        _config = StateQuarkConfig()
    return _config


def set_config(config: StateQuarkConfig) -> None:
    """Set the global configuration."""
    global _config
    _config = config
    if config.debug:
        _enable_debug()
    else:
        _disable_debug()


def enable_debug() -> None:
    """Enable debug mode."""
    config = get_config()
    config.debug = True
    _enable_debug()


def disable_debug() -> None:
    """Disable debug mode."""
    config = get_config()
    config.debug = False
    _disable_debug()


def reset_config() -> None:
    """Reset configuration to defaults."""
    global _config
    _config = StateQuarkConfig()
