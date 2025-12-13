"""StateQuark - Atomic state management for IoT and embedded systems."""

from .config import (
    StateQuarkConfig,
    disable_debug,
    enable_debug,
    get_config,
    reset_config,
    set_config,
)
from .core import Quark, batch, quark
from .executor import cleanup_executor
from .types import ErrorHandler, GetterFunction, QuarkCallback

__version__ = "0.3.0"
__all__ = [
    "Quark",
    "quark",
    "batch",
    "StateQuarkConfig",
    "get_config",
    "set_config",
    "reset_config",
    "enable_debug",
    "disable_debug",
    "cleanup_executor",
    "QuarkCallback",
    "ErrorHandler",
    "GetterFunction",
]
