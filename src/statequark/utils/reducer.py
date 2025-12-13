"""Reducer pattern for Quark state management."""

from typing import Callable, Generic

from ..atom import Quark
from ..types import T


class ReducerQuark(Quark[T], Generic[T]):
    """Quark with reducer-based state updates."""

    __slots__ = ("_reducer",)

    def __init__(
        self,
        initial: T,
        reducer: Callable[[T, any], T],
    ) -> None:
        super().__init__(initial)
        self._reducer = reducer

    def dispatch(self, action: any) -> None:
        """Dispatch an action to update state."""
        new_value = self._reducer(self._value, action)
        self.set_sync(new_value)

    async def dispatch_async(self, action: any) -> None:
        """Dispatch an action asynchronously."""
        new_value = self._reducer(self._value, action)
        await self.set(new_value)


def quark_with_reducer(
    initial: T,
    reducer: Callable[[T, any], T],
) -> ReducerQuark[T]:
    """Create a Quark with reducer pattern."""
    return ReducerQuark(initial, reducer)
