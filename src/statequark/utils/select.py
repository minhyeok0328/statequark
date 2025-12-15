"""Select (slice) utilities for partial state subscription."""

from collections.abc import Callable
from typing import Any, Generic, TypeVar

from ..quark import Quark
from ..types import T

S = TypeVar("S")


class SelectQuark(Quark[S], Generic[S]):
    """Quark that selects a slice of another Quark's value."""

    __slots__ = ("_source", "_selector", "_equals", "_unsub")

    def __init__(
        self,
        source: Quark[Any],
        selector: Callable[[Any], S],
        equals: Callable[[S, S], bool] | None = None,
    ) -> None:
        self._source = source
        self._selector = selector
        self._equals = equals or (lambda a, b: a == b)

        initial = selector(source.value)
        super().__init__(initial)
        self._unsub = source.subscribe(self._on_source_change)

    def _on_source_change(self, src: Quark[Any]) -> None:
        new_slice = self._selector(src.value)
        if not self._equals(self._value, new_slice):
            self._value = new_slice
            self._notify_sync()

    @property
    def value(self) -> S:
        return self._selector(self._source.value)

    @value.setter
    def value(self, new_value: S) -> None:
        raise AttributeError("Cannot assign to select quark. It is read-only.")

    def set(self, new_value: S) -> None:
        raise ValueError("Cannot set select quark directly")

    async def set_async(self, new_value: S) -> None:
        raise ValueError("Cannot set select quark directly")

    def cleanup(self) -> None:
        self._unsub()
        super().cleanup()


def select(
    source: Quark[T],
    selector: Callable[[T], S],
    equals: Callable[[S, S], bool] | None = None,
) -> SelectQuark[S]:
    """Create a Quark that selects a slice of source Quark."""
    return SelectQuark(source, selector, equals)
