"""Subscription and notification system for StateQuark."""

import asyncio
import threading
from typing import TYPE_CHECKING

from .executor import get_shared_executor
from .logger import log_debug, log_error

if TYPE_CHECKING:
    from .types import ErrorHandler, QuarkCallback


class SubscriptionMixin:
    """Mixin providing subscription and notification capabilities."""

    _callbacks: list["QuarkCallback"]
    _error_handler: "ErrorHandler | None"
    _id: int
    _lock: threading.RLock

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

    def set_error_handler(self, handler: "ErrorHandler | None") -> None:
        """Set custom error handler for callback exceptions."""
        with self._lock:
            self._error_handler = handler
