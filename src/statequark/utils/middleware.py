"""Middleware system for Quark state changes."""

from collections.abc import Callable
from typing import Any, Generic

from ..atom import Quark
from ..types import T

Middleware = Callable[[T, T, Callable[[T], None]], None]


class MiddlewareQuark(Quark[T], Generic[T]):
    """Quark with middleware pipeline for state changes."""

    __slots__ = ("_middlewares",)

    def __init__(self, initial: T) -> None:
        super().__init__(initial)
        self._middlewares: list[Middleware[T]] = []

    def use(self, middleware: Middleware[T]) -> "MiddlewareQuark[T]":
        """Add middleware. Returns self for chaining."""
        self._middlewares.append(middleware)
        return self

    def set_sync(self, new_value: T) -> None:
        if not self._middlewares:
            super().set_sync(new_value)
            return

        def create_next(index: int) -> Callable[[T], None]:
            def next_fn(value: T) -> None:
                if index >= len(self._middlewares):
                    super(MiddlewareQuark, self).set_sync(value)
                else:
                    self._middlewares[index](self._value, value, create_next(index + 1))

            return next_fn

        create_next(0)(new_value)


def middleware(initial: T) -> MiddlewareQuark[T]:
    """Create a Quark with middleware support."""
    return MiddlewareQuark(initial)


def logger(name: str = "quark") -> Middleware[Any]:
    """Middleware that logs state changes."""

    def log_middleware(old: Any, new: Any, next_fn: Callable[[Any], None]) -> None:
        print(f"[{name}] {old} -> {new}")
        next_fn(new)

    return log_middleware


def persist(storage: dict[str, Any], key: str) -> Middleware[Any]:
    """Middleware that persists state to a dict."""

    def persist_middleware(old: Any, new: Any, next_fn: Callable[[Any], None]) -> None:
        next_fn(new)
        storage[key] = new

    return persist_middleware
