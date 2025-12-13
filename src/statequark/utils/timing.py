"""Timing utilities for sensor noise filtering."""

import threading
import time
from typing import Generic

from ..atom import Quark
from ..types import T


class DebouncedQuark(Quark[T], Generic[T]):
    """Quark that debounces rapid value changes."""

    __slots__ = ("_delay", "_timer", "_pending", "_timer_lock")

    def __init__(self, initial: T, delay: float) -> None:
        super().__init__(initial)
        self._delay = delay
        self._timer: threading.Timer | None = None
        self._pending: T | None = None
        self._timer_lock = threading.Lock()

    def set_sync(self, new_value: T) -> None:
        with self._timer_lock:
            self._pending = new_value
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(self._delay, self._flush)
            self._timer.start()

    def _flush(self) -> None:
        with self._timer_lock:
            if self._pending is not None:
                super().set_sync(self._pending)
                self._pending = None
                self._timer = None

    def flush_now(self) -> None:
        """Force immediate flush of pending value."""
        with self._timer_lock:
            if self._timer:
                self._timer.cancel()
        self._flush()

    def cleanup(self) -> None:
        with self._timer_lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None
        super().cleanup()


class ThrottledQuark(Quark[T], Generic[T]):
    """Quark that throttles value updates to a maximum rate."""

    __slots__ = ("_interval", "_last_update", "_throttle_lock")

    def __init__(self, initial: T, interval: float) -> None:
        super().__init__(initial)
        self._interval = interval
        self._last_update = 0.0
        self._throttle_lock = threading.Lock()

    def set_sync(self, new_value: T) -> None:
        with self._throttle_lock:
            now = time.monotonic()
            if now - self._last_update >= self._interval:
                self._last_update = now
                super().set_sync(new_value)

    def force_set(self, new_value: T) -> None:
        """Force update regardless of throttle."""
        with self._throttle_lock:
            self._last_update = time.monotonic()
        super().set_sync(new_value)


def debounce(initial: T, delay: float) -> DebouncedQuark[T]:
    """Create a debounced Quark (waits for silence before updating)."""
    return DebouncedQuark(initial, delay)


def throttle(initial: T, interval: float) -> ThrottledQuark[T]:
    """Create a throttled Quark (limits update frequency)."""
    return ThrottledQuark(initial, interval)
