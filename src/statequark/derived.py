"""Derived state computation for StateQuark."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from .batch import add_to_batch, is_batch_active
from .logger import log_error

if TYPE_CHECKING:
    from .quark import Quark


class DerivedMixin:
    """Mixin providing derived state computation capabilities."""

    _getter: Callable[[Callable[["Quark[Any]"], Any]], Any] | None
    _deps: list["Quark[Any]"]
    _unsubscribers: list[Callable[[], None]]
    _id: int

    def _notify_sync(self) -> None:
        """Notify subscribers synchronously. Provided by SubscriptionMixin."""
        ...

    def _compute(self) -> Any:
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
        if is_batch_active():
            add_to_batch(self._id, cast("Quark[Any]", self))
        else:
            self._notify_sync()

    def _setup_dependencies(self) -> None:
        """Subscribe to all dependencies and store unsubscribe functions."""
        for dep in self._deps:
            unsub = dep.subscribe(self._on_dep_change)
            self._unsubscribers.append(unsub)

    def _cleanup_dependencies(self) -> None:
        """Unsubscribe from all dependencies."""
        from .logger import log_warning

        for unsub in self._unsubscribers:
            try:
                unsub()
            except Exception as e:
                log_warning("Quark #%d: cleanup error: %s", self._id, e)
        self._unsubscribers.clear()
