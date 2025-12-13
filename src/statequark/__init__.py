"""StateQuark - Atomic state management for IoT and embedded systems."""

from .atom import Quark
from .batch import batch
from .config import (
    StateQuarkConfig,
    disable_debug,
    enable_debug,
    get_config,
    reset_config,
    set_config,
)
from .executor import cleanup_executor
from .types import ErrorHandler, GetterFunction, QuarkCallback
from .factory import quark
from .utils import (
    debounce,
    loadable,
    Loadable,
    quark_family,
    quark_with_reducer,
    quark_with_storage,
    select,
    throttle,
)

__version__ = "0.4.0"
__all__ = [
    # Core
    "Quark",
    "quark",
    "batch",
    # Config
    "StateQuarkConfig",
    "get_config",
    "set_config",
    "reset_config",
    "enable_debug",
    "disable_debug",
    "cleanup_executor",
    # Types
    "QuarkCallback",
    "ErrorHandler",
    "GetterFunction",
    # Utils
    "quark_with_storage",
    "quark_with_reducer",
    "select",
    "loadable",
    "Loadable",
    "quark_family",
    "debounce",
    "throttle",
]
