"""Type definitions for StateQuark."""

from typing import TYPE_CHECKING, Any, Callable, Protocol, TypeVar

if TYPE_CHECKING:
    from .core import Quark

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class QuarkProtocol(Protocol[T_co]):
    """Protocol for Quark interface."""

    @property
    def value(self) -> T_co: ...


if TYPE_CHECKING:
    QuarkCallback = Callable[["Quark[Any]"], None]
    ErrorHandler = Callable[[Exception, QuarkCallback, "Quark[Any]"], None]
    GetterFunction = Callable[[Callable[["Quark[Any]"], Any]], T]
else:
    QuarkCallback = Callable[[Any], None]
    ErrorHandler = Callable[[Exception, Any, Any], None]
    GetterFunction = Callable[[Callable[[Any], Any]], Any]
