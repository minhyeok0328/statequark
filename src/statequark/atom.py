"""Core Quark atom implementation for atomic state management."""

import threading
from typing import TYPE_CHECKING, Any, Callable, Generic, Optional, Union, cast

from .batch import add_to_batch, is_batch_active
from .derived import DerivedMixin
from .logger import log_debug
from .store import SubscriptionMixin
from .types import T

if TYPE_CHECKING:
    from .types import ErrorHandler, QuarkCallback


class Quark(SubscriptionMixin, DerivedMixin, Generic[T]):
    """
    Reactive state container with automatic dependency tracking.

    Thread-safe atomic state for IoT and embedded systems.
    """

    __slots__ = (
        "_value",
        "_initial",
        "_callbacks",
        "_lock",
        "_getter",
        "_deps",
        "_error_handler",
        "_id",
    )

    _instance_counter: int = 0
    _counter_lock: threading.Lock = threading.Lock()

    def __init__(
        self,
        initial_or_getter: Union[T, Callable[[Callable[["Quark[Any]"], Any]], T]],
        deps: Optional[list["Quark[Any]"]] = None,
        error_handler: Optional["ErrorHandler"] = None,
    ) -> None:
        """
        Initialize a Quark.

        Args:
            initial_or_getter: Initial value or getter function for derived quarks.
            deps: Dependencies for derived quarks.
            error_handler: Custom error handler for callbacks.

        Raises:
            ValueError: If getter provided without dependencies.
        """
        with Quark._counter_lock:
            Quark._instance_counter += 1
            self._id = Quark._instance_counter

        self._lock = threading.RLock()
        self._callbacks: list[QuarkCallback] = []
        self._deps: list[Quark[Any]] = deps or []
        self._error_handler = error_handler

        if callable(initial_or_getter):
            if not self._deps:
                raise ValueError("Derived quarks require at least one dependency")
            self._getter: Optional[Callable[[Callable[["Quark[Any]"], Any]], T]] = (
                initial_or_getter
            )
            self._initial: Optional[T] = None
            self._value: T = self._compute()

            log_debug(
                "Created derived Quark #%d with %d deps", self._id, len(self._deps)
            )

            self._setup_dependencies()
        else:
            self._getter = None
            self._initial = initial_or_getter
            self._value = initial_or_getter

            log_debug("Created Quark #%d: %r", self._id, initial_or_getter)

    @property
    def value(self) -> T:
        """Current value. Recomputes for derived quarks."""
        if self._getter:
            with self._lock:
                return cast(T, self._compute())
        return self._value

    def set_sync(self, new_value: T) -> None:
        """Set value synchronously. Raises ValueError on derived quark."""
        with self._lock:
            if self._getter:
                raise ValueError("Cannot set derived quark directly")
            old_value = self._value
            self._value = new_value
            log_debug("Quark #%d: %r -> %r", self._id, old_value, new_value)

        if is_batch_active():
            add_to_batch(self._id, self)
        else:
            self._notify_sync()

    async def set(self, new_value: T) -> None:
        """Set value asynchronously. Raises ValueError on derived quark."""
        with self._lock:
            if self._getter:
                raise ValueError("Cannot set derived quark directly")
            old_value = self._value
            self._value = new_value
            log_debug("Quark #%d (async): %r -> %r", self._id, old_value, new_value)

        await self._notify()

    def reset(self) -> None:
        """Reset to initial value. Raises ValueError on derived quark."""
        if self._getter:
            raise ValueError("Cannot reset derived quark")
        if self._initial is not None:
            self.set_sync(self._initial)

    def cleanup(self) -> None:
        """Release resources. Essential for long-running IoT applications."""
        with self._lock:
            log_debug("Quark #%d: cleanup", self._id)
            self._cleanup_dependencies()
            self._deps.clear()
            self._callbacks.clear()

    def __repr__(self) -> str:
        return f"Quark(value={self.value!r})"

    def __enter__(self) -> "Quark[T]":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.cleanup()
