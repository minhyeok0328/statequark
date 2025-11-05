"""
Type definitions for StateQuark.

This module contains all type definitions, protocols, and type aliases used
throughout the StateQuark library.
"""

from typing import TYPE_CHECKING, Any, Callable, Protocol, TypeVar

if TYPE_CHECKING:
    from .core import Quark

# Type variables
T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class QuarkProtocol(Protocol[T_co]):
    """Protocol defining the interface for Quark instances."""

    @property
    def value(self) -> T_co:
        """Get the current value of the quark."""
        ...


# Callback and handler types
if TYPE_CHECKING:
    QuarkCallback = Callable[["Quark[Any]"], None]
    ErrorHandler = Callable[[Exception, QuarkCallback, "Quark[Any]"], None]
    GetterFunction = Callable[[Callable[["Quark[Any]"], Any]], T]
else:
    QuarkCallback = Callable[[Any], None]
    ErrorHandler = Callable[[Exception, Any, Any], None]
    GetterFunction = Callable[[Callable[[Any], Any]], Any]
