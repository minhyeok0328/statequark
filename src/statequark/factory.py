"""Factory functions and utilities for StateQuark."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Generic, Optional, overload

from .quark import Quark
from .types import T

if TYPE_CHECKING:
    from .types import ErrorHandler


class _TypedQuarkFactory(Generic[T]):
    """Factory for creating typed Quark instances via quark[Type](value) syntax."""

    __slots__ = ()

    def __call__(
        self,
        initial_or_getter: T | Callable[[Callable[[Quark[Any]], Any]], T],
        deps: list[Quark[Any]] | None = None,
        error_handler: Optional["ErrorHandler"] = None,
    ) -> Quark[T]:
        return Quark(initial_or_getter, deps, error_handler)


class QuarkFactory:
    """
    Factory for creating Quark instances with optional type hints.

    Supports both styles:
        count = quark(0)           # Type inferred as Quark[int]
        count = quark[int](0)      # Explicit type hint

    Useful for cases where type inference is insufficient:
        user = quark[User | None](None)
        items = quark[list[str]]([])
    """

    __slots__ = ()

    @overload
    def __call__(
        self,
        initial_or_getter: T,
        deps: None = None,
        error_handler: Optional["ErrorHandler"] = None,
    ) -> Quark[T]: ...

    @overload
    def __call__(
        self,
        initial_or_getter: Callable[[Callable[[Quark[Any]], Any]], T],
        deps: list[Quark[Any]],
        error_handler: Optional["ErrorHandler"] = None,
    ) -> Quark[T]: ...

    def __call__(
        self,
        initial_or_getter: T | Callable[[Callable[[Quark[Any]], Any]], T],
        deps: list[Quark[Any]] | None = None,
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

    def __getitem__(self, type_hint: type[T]) -> _TypedQuarkFactory[T]:
        """
        Enable quark[Type](value) syntax for explicit type hints.

        Example:
            user = quark[User | None](None)
            items = quark[list[str]]([])
        """
        return _TypedQuarkFactory[T]()


quark = QuarkFactory()
