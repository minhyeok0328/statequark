"""Factory functions and utilities for StateQuark."""

from typing import TYPE_CHECKING, Any, Callable, Optional, Union

from .atom import Quark
from .types import T

if TYPE_CHECKING:
    from .types import ErrorHandler


def quark(
    initial_or_getter: Union[T, Callable[[Callable[[Quark[Any]], Any]], T]],
    deps: Optional[list[Quark[Any]]] = None,
    error_handler: Optional["ErrorHandler"] = None,
) -> Quark[T]:
    """
    Create a new Quark instance.

    Args:
        initial_or_getter: Initial value or getter function for derived quarks.
        deps: Dependencies for derived quarks.
        error_handler: Custom error handler for callbacks.

    Returns:
        A new Quark instance.

    Example:
        # Basic quark
        count = quark(0)

        # Derived quark
        doubled = quark(lambda get: get(count) * 2, deps=[count])
    """
    return Quark(initial_or_getter, deps, error_handler)
