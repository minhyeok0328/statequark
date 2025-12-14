"""Loadable wrapper for async state handling."""

from dataclasses import dataclass
from typing import Generic, Literal, TypeAlias

from ..quark import Quark
from ..types import T


@dataclass(frozen=True, slots=True)
class LoadableLoading:
    state: Literal["loading"] = "loading"


@dataclass(frozen=True, slots=True)
class LoadableHasData(Generic[T]):
    data: T
    state: Literal["hasData"] = "hasData"


@dataclass(frozen=True, slots=True)
class LoadableHasError:
    error: Exception
    state: Literal["hasError"] = "hasError"


Loadable: TypeAlias = LoadableLoading | LoadableHasData[T] | LoadableHasError


class LoadableQuark(Quark[Loadable[T]], Generic[T]):
    """Quark that wraps async values with loading/error states."""

    __slots__ = ("_source",)

    def __init__(self, source: Quark[T]) -> None:
        self._source = source
        super().__init__(LoadableHasData(data=source.value))
        source.subscribe(self._on_source_change)

    def _on_source_change(self, src: Quark[T]) -> None:
        self._value = LoadableHasData(data=src.value)
        self._notify_sync()

    def set_loading(self) -> None:
        """Set state to loading."""
        self._value = LoadableLoading()
        self._notify_sync()

    def set_error(self, error: Exception) -> None:
        """Set state to error."""
        self._value = LoadableHasError(error=error)
        self._notify_sync()

    def set_data(self, data: T) -> None:
        """Set state to hasData."""
        self._value = LoadableHasData(data=data)
        self._notify_sync()

    def cleanup(self) -> None:
        self._source.unsubscribe(self._on_source_change)
        super().cleanup()


def loadable(source: Quark[T]) -> LoadableQuark[T]:
    """Wrap a Quark with loading/error state tracking."""
    return LoadableQuark(source)
