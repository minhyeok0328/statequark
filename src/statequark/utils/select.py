"""Select (slice) utilities for partial state subscription."""

from collections.abc import Callable
from typing import Any, Generic, TypeVar

from ..atom import Quark
from ..types import T

S = TypeVar("S")


class SelectQuark(Quark[S], Generic[S]):
    """Quark that selects a slice of another Quark's value."""

    __slots__ = ("_source", "_selector", "_equals", "_last_source")

    def __init__(
        self,
        source: Quark[Any],
        selector: Callable[[Any], S],
        equals: Callable[[S, S], bool] | None = None,
    ) -> None:
        self._source = source
        self._selector = selector
        self._equals = equals or (lambda a, b: a == b)
        self._last_source = source.value

        initial = selector(source.value)
        super().__init__(initial)
        source.subscribe(self._on_source_change)

    def _on_source_change(self, src: Quark[Any]) -> None:
        new_slice = self._selector(src.value)
        if not self._equals(self._value, new_slice):
            self._value = new_slice
            self._notify_sync()

    @property
    def value(self) -> S:
        return self._selector(self._source.value)

    def set(self, new_value: S) -> None:
        raise ValueError("Cannot set select quark directly")

    async def set_async(self, new_value: S) -> None:
        raise ValueError("Cannot set select quark directly")

    def cleanup(self) -> None:
        self._source.unsubscribe(self._on_source_change)
        super().cleanup()


def select(
    source: Quark[T],
    selector: Callable[[T], S],
    equals: Callable[[S, S], bool] | None = None,
) -> SelectQuark[S]:
    """Create a Quark that selects a slice of source Quark."""
    return SelectQuark(source, selector, equals)
