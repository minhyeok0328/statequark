"""Batch update system for StateQuark."""

import threading
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator

if TYPE_CHECKING:
    from .atom import Quark

# Batch update context
_batch_lock = threading.Lock()
_batch_active = threading.local()
_batch_pending: dict[int, "Quark[Any]"] = {}


def is_batch_active() -> bool:
    """Check if batch update is active in current thread."""
    return getattr(_batch_active, "active", False)


def add_to_batch(quark_id: int, quark: "Quark[Any]") -> None:
    """Add a quark to the pending batch updates."""
    _batch_pending[quark_id] = quark


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
