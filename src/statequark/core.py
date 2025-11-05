"""
Core Quark implementation for StateQuark.

This module contains the main Quark class for atomic state management,
optimized for IoT devices and embedded systems.
"""

import asyncio
import threading
from typing import TYPE_CHECKING, Any, Callable, Generic, Optional, Union

from .executor import get_shared_executor
from .logger import log_debug, log_error, log_warning
from .types import T

if TYPE_CHECKING:
    from .types import ErrorHandler, QuarkCallback


class Quark(Generic[T]):
    """
    A reactive state container with automatic dependency tracking.

    Quark provides atomic state management with thread-safe operations,
    subscriptions, and derived state calculations. It's designed for
    resource-constrained IoT and embedded systems.

    Type Parameters:
        T: The type of value stored in the quark.

    Attributes:
        value: The current value of the quark (read-only property).

    Example:
        >>> # Simple state
        >>> temperature = Quark(20.0)
        >>> temperature.value
        20.0
        >>> temperature.set_sync(25.5)
        >>> temperature.value
        25.5

        >>> # Derived state
        >>> celsius = Quark(25.0)
        >>> fahrenheit = Quark(lambda get: get(celsius) * 9/5 + 32, deps=[celsius])
        >>> fahrenheit.value
        77.0
    """

    __slots__ = (
        "_value",
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
        Initialize a Quark instance.

        Args:
            initial_or_getter: Initial value or getter function for derived quarks.
            deps: List of dependent quarks (required for derived quarks).
            error_handler: Optional custom error handler for callback exceptions.

        Raises:
            ValueError: If getter function is provided without dependencies.

        Example:
            >>> # Regular quark
            >>> count = Quark(0)

            >>> # Derived quark
            >>> base = Quark(5)
            >>> doubled = Quark(lambda get: get(base) * 2, deps=[base])
        """
        # Generate unique ID
        with Quark._counter_lock:
            Quark._instance_counter += 1
            self._id = Quark._instance_counter

        self._lock = threading.RLock()
        self._callbacks: list[QuarkCallback] = []
        self._deps = deps or []
        self._error_handler = error_handler

        is_callable = callable(initial_or_getter)

        if is_callable:
            if not self._deps:
                raise ValueError(
                    "Getter function provided but no dependencies specified. "
                    "Derived quarks must have at least one dependency."
                )
            self._getter: Optional[
                Callable[[Callable[["Quark[Any]"], Any]], T]
            ] = initial_or_getter  # type: ignore
            self._value = self._compute()

            log_debug(
                "Created derived Quark #%d with %d dependencies",
                self._id,
                len(self._deps),
            )

            # Subscribe to dependency changes
            for dep in self._deps:
                dep.subscribe(self._on_dep_change)
        else:
            self._getter = None
            self._value: T = initial_or_getter  # type: ignore

            log_debug(
                "Created Quark #%d with initial value: %r", self._id, initial_or_getter
            )

    @property
    def value(self) -> T:
        """
        Get the current value of the quark.

        For derived quarks, this recomputes the value based on current
        dependencies.

        Returns:
            T: The current value.

        Example:
            >>> temp = Quark(20.0)
            >>> temp.value
            20.0
        """
        with self._lock:
            if self._getter:
                return self._compute()
            return self._value

    def set(self, new_value: T) -> None:
        """
        Synchronously set a new value and notify subscribers.

        This method is thread-safe and will block until all callbacks
        have been executed.

        Args:
            new_value: The new value to set.

        Raises:
            ValueError: If called on a derived quark.

        Example:
            >>> temp = Quark(20.0)
            >>> temp.set(25.5)
            >>> temp.value
            25.5
        """
        with self._lock:
            if self._getter:
                raise ValueError("Cannot set derived quark directly")

            old_value = self._value
            self._value = new_value

            log_debug(
                "Quark #%d value changed: %r -> %r",
                self._id,
                old_value,
                new_value,
            )

        self._notify_sync()

    async def set_async(self, new_value: T) -> None:
        """
        Asynchronously set a new value and notify subscribers.

        This method is thread-safe and will execute callbacks asynchronously
        in the shared thread pool.

        Args:
            new_value: The new value to set.

        Raises:
            ValueError: If called on a derived quark.

        Example:
            >>> temp = Quark(20.0)
            >>> await temp.set_async(25.5)
            >>> temp.value
            25.5
        """
        with self._lock:
            if self._getter:
                raise ValueError("Cannot set derived quark directly")

            old_value = self._value
            self._value = new_value

            log_debug(
                "Quark #%d value changed (async): %r -> %r",
                self._id,
                old_value,
                new_value,
            )

        await self._notify()

    def subscribe(self, callback: "QuarkCallback") -> None:
        """
        Subscribe to value changes.

        The callback will be called whenever the quark's value changes.
        Duplicate callbacks are automatically prevented.

        Args:
            callback: Function to call when value changes. Receives the quark
                     instance as an argument.

        Example:
            >>> def on_change(q):
            ...     print(f"Value changed to {q.value}")
            >>> temp = Quark(20.0)
            >>> temp.subscribe(on_change)
            >>> temp.set_sync(25.0)
            Value changed to 25.0
        """
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)
                log_debug(
                    "Quark #%d: subscribed callback %s (total: %d)",
                    self._id,
                    callback.__name__,
                    len(self._callbacks),
                )

    def unsubscribe(self, callback: "QuarkCallback") -> None:
        """
        Unsubscribe from value changes.

        Args:
            callback: The callback function to remove.

        Example:
            >>> def on_change(q):
            ...     print(f"Value: {q.value}")
            >>> temp = Quark(20.0)
            >>> temp.subscribe(on_change)
            >>> temp.unsubscribe(on_change)
        """
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
                log_debug(
                    "Quark #%d: unsubscribed callback %s (remaining: %d)",
                    self._id,
                    callback.__name__,
                    len(self._callbacks),
                )

    def cleanup(self) -> None:
        """
        Clean up resources to prevent memory leaks.

        This method removes all dependencies and callbacks, breaking circular
        references. Essential for long-running IoT applications.

        Example:
            >>> temp = Quark(20.0)
            >>> # ... use the quark ...
            >>> temp.cleanup()
        """
        with self._lock:
            log_debug("Quark #%d: cleaning up resources", self._id)

            # Remove from dependencies
            for dep in self._deps:
                try:
                    dep.unsubscribe(self._on_dep_change)
                except Exception as e:
                    log_warning(
                        "Quark #%d: error unsubscribing from dependency: %s",
                        self._id,
                        str(e),
                    )

            # Clear all references
            self._deps.clear()
            self._callbacks.clear()

            log_debug("Quark #%d: cleanup complete", self._id)

    def set_error_handler(self, handler: Optional["ErrorHandler"]) -> None:
        """
        Set or update the custom error handler for callback exceptions.

        Args:
            handler: Error handler function or None to use default handling.

        Example:
            >>> def error_handler(error, callback, quark):
            ...     print(f"Error in {callback.__name__}: {error}")
            >>> temp = Quark(20.0)
            >>> temp.set_error_handler(error_handler)
        """
        with self._lock:
            self._error_handler = handler
            log_debug("Quark #%d: error handler updated", self._id)

    def _compute(self) -> T:
        """
        Compute the value for a derived quark.

        Returns:
            T: The computed value.

        Raises:
            ValueError: If called on a non-derived quark.
        """
        if self._getter is None:
            raise ValueError("Cannot compute value for non-derived quark")

        def get(dep_quark: "Quark[Any]") -> Any:
            """Getter function passed to derived quark computations."""
            return dep_quark.value

        try:
            result = self._getter(get)
            log_debug("Quark #%d: computed value: %r", self._id, result)
            return result
        except Exception as e:
            log_error("Quark #%d: error computing value: %s", self._id, str(e))
            raise

    def _on_dep_change(self, dep: "Quark[Any]") -> None:
        """
        Handle dependency changes for derived quarks.

        Args:
            dep: The dependency quark that changed.
        """
        log_debug("Quark #%d: dependency changed, notifying subscribers", self._id)
        self._notify_sync()

    async def _notify(self) -> None:
        """Asynchronously notify all subscribers of a value change."""
        with self._lock:
            callbacks_copy = self._callbacks[:]

        if not callbacks_copy:
            return

        log_debug(
            "Quark #%d: notifying %d subscribers (async)", self._id, len(callbacks_copy)
        )

        executor = get_shared_executor()
        await asyncio.gather(
            *[
                asyncio.get_event_loop().run_in_executor(executor, self._safe_call, cb)
                for cb in callbacks_copy
            ]
        )

    def _notify_sync(self) -> None:
        """Synchronously notify all subscribers of a value change."""
        with self._lock:
            callbacks_copy = self._callbacks[:]

        if not callbacks_copy:
            return

        log_debug(
            "Quark #%d: notifying %d subscribers (sync)", self._id, len(callbacks_copy)
        )

        for cb in callbacks_copy:
            self._safe_call(cb)

    def _safe_call(self, callback: "QuarkCallback") -> None:
        """
        Safely execute a callback with error handling.

        Args:
            callback: The callback to execute.
        """
        try:
            log_debug("Quark #%d: executing callback %s", self._id, callback.__name__)
            callback(self)
        except Exception as e:
            log_error(
                "Quark #%d: callback %s raised exception: %s",
                self._id,
                callback.__name__,
                str(e),
            )

            if self._error_handler:
                try:
                    self._error_handler(e, callback, self)
                except Exception as handler_error:
                    log_error(
                        "Quark #%d: error handler failed: %s (original error: %s)",
                        self._id,
                        str(handler_error),
                        str(e),
                    )
            else:
                # Default error handling - just log
                log_warning(
                    "Quark #%d: no error handler set, exception ignored",
                    self._id,
                )

    def __repr__(self) -> str:
        """
        Return string representation of the quark.

        Returns:
            str: String representation showing the current value.
        """
        return f"Quark(value={self.value!r})"

    def __enter__(self) -> "Quark[T]":
        """
        Enter context manager.

        Returns:
            Quark[T]: Self for use in with statement.

        Example:
            >>> with Quark(20.0) as temp:
            ...     temp.set_sync(25.0)
            ...     print(temp.value)
            25.0
        """
        log_debug("Quark #%d: entering context", self._id)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit context manager and cleanup resources.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        log_debug("Quark #%d: exiting context, cleaning up", self._id)
        self.cleanup()


def quark(
    initial_or_getter: Union[T, Callable[[Callable[[Quark[Any]], Any]], T]],
    deps: Optional[list[Quark[Any]]] = None,
    error_handler: Optional["ErrorHandler"] = None,
) -> Quark[T]:
    """
    Create a new Quark instance.

    This is a convenience function that creates a Quark instance with
    a cleaner syntax.

    Args:
        initial_or_getter: Initial value or getter function for derived quarks.
        deps: List of dependent quarks (required for derived quarks).
        error_handler: Optional custom error handler for callback exceptions.

    Returns:
        Quark[T]: A new Quark instance.

    Example:
        >>> # Simple quark
        >>> count = quark(0)

        >>> # Derived quark
        >>> base = quark(5)
        >>> doubled = quark(lambda get: get(base) * 2, deps=[base])
        >>> doubled.value
        10
    """
    return Quark(initial_or_getter, deps, error_handler)
