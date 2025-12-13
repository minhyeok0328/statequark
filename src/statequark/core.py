"""Core Quark implementation for atomic state management."""

import asyncio
import threading
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Callable, Generator, Generic, Optional, Union

from .executor import get_shared_executor
from .logger import log_debug, log_error, log_warning
from .types import T

if TYPE_CHECKING:
    from .types import ErrorHandler, QuarkCallback


# Batch update context
_batch_lock = threading.Lock()
_batch_active = threading.local()
_batch_pending: dict[int, "Quark[Any]"] = {}


class Quark(Generic[T]):
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
        self._deps = deps or []
        self._error_handler = error_handler

        if callable(initial_or_getter):
            if not self._deps:
                raise ValueError("Derived quarks require at least one dependency")
            self._getter: Optional[Callable[[Callable[["Quark[Any]"], Any]], T]] = (
                initial_or_getter
            )
            self._initial = None
            self._value: T = self._compute()

            log_debug(
                "Created derived Quark #%d with %d deps", self._id, len(self._deps)
            )

            for dep in self._deps:
                dep.subscribe(self._on_dep_change)
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
                return self._compute()
        return self._value

    def set_sync(self, new_value: T) -> None:
        """Set value synchronously. Raises ValueError on derived quark."""
        with self._lock:
            if self._getter:
                raise ValueError("Cannot set derived quark directly")
            old_value = self._value
            self._value = new_value
            log_debug("Quark #%d: %r -> %r", self._id, old_value, new_value)

        if _is_batch_active():
            _batch_pending[self._id] = self
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

    def subscribe(self, callback: "QuarkCallback") -> None:
        """Subscribe to value changes. Duplicates are ignored."""
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)
                log_debug(
                    "Quark #%d: +subscriber (%d total)", self._id, len(self._callbacks)
                )

    def unsubscribe(self, callback: "QuarkCallback") -> None:
        """Unsubscribe from value changes."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
                log_debug(
                    "Quark #%d: -subscriber (%d remaining)",
                    self._id,
                    len(self._callbacks),
                )

    def cleanup(self) -> None:
        """Release resources. Essential for long-running IoT applications."""
        with self._lock:
            log_debug("Quark #%d: cleanup", self._id)
            for dep in self._deps:
                try:
                    dep.unsubscribe(self._on_dep_change)
                except Exception as e:
                    log_warning("Quark #%d: cleanup error: %s", self._id, e)
            self._deps.clear()
            self._callbacks.clear()

    def set_error_handler(self, handler: Optional["ErrorHandler"]) -> None:
        """Set custom error handler for callback exceptions."""
        with self._lock:
            self._error_handler = handler

    def _compute(self) -> T:
        """Compute derived value."""
        if self._getter is None:
            raise ValueError("Cannot compute non-derived quark")

        def get(dep: "Quark[Any]") -> Any:
            return dep.value

        try:
            return self._getter(get)
        except Exception as e:
            log_error("Quark #%d: compute error: %s", self._id, e)
            raise

    def _on_dep_change(self, dep: "Quark[Any]") -> None:
        """Handle dependency change."""
        if _is_batch_active():
            _batch_pending[self._id] = self
        else:
            self._notify_sync()

    async def _notify(self) -> None:
        """Notify subscribers asynchronously."""
        with self._lock:
            callbacks = self._callbacks[:]

        if not callbacks:
            return

        log_debug("Quark #%d: notify %d (async)", self._id, len(callbacks))
        executor = get_shared_executor()
        loop = asyncio.get_running_loop()
        await asyncio.gather(
            *[loop.run_in_executor(executor, self._safe_call, cb) for cb in callbacks]
        )

    def _notify_sync(self) -> None:
        """Notify subscribers synchronously."""
        with self._lock:
            callbacks = self._callbacks[:]

        if not callbacks:
            return

        log_debug("Quark #%d: notify %d (sync)", self._id, len(callbacks))
        for cb in callbacks:
            self._safe_call(cb)

    def _safe_call(self, callback: "QuarkCallback") -> None:
        """Execute callback with error handling."""
        try:
            callback(self)
        except Exception as e:
            log_error("Quark #%d: callback error: %s", self._id, e)
            if self._error_handler:
                try:
                    self._error_handler(e, callback, self)
                except Exception as he:
                    log_error("Quark #%d: error handler failed: %s", self._id, he)

    def __repr__(self) -> str:
        return f"Quark(value={self.value!r})"

    def __enter__(self) -> "Quark[T]":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.cleanup()


def quark(
    initial_or_getter: Union[T, Callable[[Callable[[Quark[Any]], Any]], T]],
    deps: Optional[list[Quark[Any]]] = None,
    error_handler: Optional["ErrorHandler"] = None,
) -> Quark[T]:
    """Create a new Quark instance."""
    return Quark(initial_or_getter, deps, error_handler)


def _is_batch_active() -> bool:
    """Check if batch update is active in current thread."""
    return getattr(_batch_active, "active", False)


@contextmanager
def batch() -> Generator[None, None, None]:
    """
    Batch multiple updates into single notification pass.

    Example:
        with batch():
            sensor1.set_sync(25.0)
            sensor2.set_sync(60.0)
            # Callbacks fire once at end, not twice
    """
    _batch_active.active = True
    try:
        yield
    finally:
        _batch_active.active = False
        with _batch_lock:
            pending = list(_batch_pending.values())
            _batch_pending.clear()

        for q in pending:
            q._notify_sync()
