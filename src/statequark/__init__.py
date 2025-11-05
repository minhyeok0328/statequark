"""
StateQuark - Lightweight atomic state management for IoT and embedded systems.

StateQuark provides a simple, reactive state management solution inspired by Jotai,
optimized for resource-constrained devices like Raspberry Pi and other embedded systems.

Quick Start:
    >>> from statequark import quark
    >>> temperature = quark(20.0)
    >>> temperature.value
    20.0
    >>> temperature.set_sync(25.5)

For detailed documentation, visit: https://github.com/minhyeok0328/statequark
"""

from .config import (
    StateQuarkConfig,
    disable_debug,
    enable_debug,
    get_config,
    reset_config,
    set_config,
)
from .core import Quark, quark
from .executor import cleanup_executor
from .types import ErrorHandler, GetterFunction, QuarkCallback
from .utils import (
    FileStorage,
    StorageType,
    quark_with_default,
    quark_with_reset,
    quark_with_storage,
)

__version__ = "0.2.0"
__all__ = [
    # Core classes and functions
    "Quark",
    "quark",
    # Configuration
    "StateQuarkConfig",
    "get_config",
    "set_config",
    "reset_config",
    "enable_debug",
    "disable_debug",
    # Executor management
    "cleanup_executor",
    # Type definitions
    "QuarkCallback",
    "ErrorHandler",
    "GetterFunction",
    # Storage utilities
    "StorageType",
    "FileStorage",
    "quark_with_storage",
    "quark_with_reset",
    "quark_with_default",
]
