"""History tracking for Quark state."""

from collections import deque
from typing import Generic

from ..atom import Quark
from ..types import T


class HistoryQuark(Quark[T], Generic[T]):
    """Quark that maintains history of previous values."""

    __slots__ = ("_history", "_max_size", "_position")

    def __init__(self, initial: T, max_size: int = 10) -> None:
        super().__init__(initial)
        self._history: deque[T] = deque([initial], maxlen=max_size + 1)
        self._max_size = max_size
        self._position = 0

    def set(self, new_value: T) -> None:
        # Truncate future history if we're not at the end
        while self._position > 0:
            self._history.popleft()
            self._position -= 1
        self._history.appendleft(new_value)
        super().set(new_value)

    def undo(self) -> bool:
        """Go back to previous value. Returns False if at oldest."""
        if self._position >= len(self._history) - 1:
            return False
        self._position += 1
        self._value = self._history[self._position]
        self._notify_sync()
        return True

    def redo(self) -> bool:
        """Go forward to next value. Returns False if at newest."""
        if self._position <= 0:
            return False
        self._position -= 1
        self._value = self._history[self._position]
        self._notify_sync()
        return True

    def can_undo(self) -> bool:
        return self._position < len(self._history) - 1

    def can_redo(self) -> bool:
        return self._position > 0

    def history_list(self) -> list[T]:
        """Get history as list (newest first)."""
        return list(self._history)

    @property
    def history_size(self) -> int:
        return len(self._history)


def history(initial: T, max_size: int = 10) -> HistoryQuark[T]:
    """Create a Quark with undo/redo history."""
    return HistoryQuark(initial, max_size)
