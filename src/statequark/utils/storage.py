"""Persistent storage for Quark state."""

import json
import os
from pathlib import Path
from typing import Any, Callable, Generic, Optional, Protocol, Union, cast

from ..atom import Quark
from ..types import T


class Storage(Protocol[T]):
    """Storage backend protocol."""

    def get(self, key: str, default: T) -> T: ...
    def set(self, key: str, value: T) -> None: ...


class FileStorage(Generic[T]):
    """JSON file-based storage for IoT devices."""

    def __init__(self, directory: Union[str, Path] = ".statequark") -> None:
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self._dir / f"{key}.json"

    def get(self, key: str, default: T) -> T:
        path = self._path(key)
        if not path.exists():
            return default
        try:
            with open(path, "r") as f:
                return cast(T, json.load(f))
        except (json.JSONDecodeError, OSError):
            return default

    def set(self, key: str, value: T) -> None:
        try:
            with open(self._path(key), "w") as f:
                json.dump(value, f)
        except OSError:
            pass


class MemoryStorage(Generic[T]):
    """In-memory storage (for testing or volatile state)."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def get(self, key: str, default: T) -> T:
        return cast(T, self._data.get(key, default))

    def set(self, key: str, value: T) -> None:
        self._data[key] = value


_default_storage: Optional[FileStorage[Any]] = None


def get_default_storage() -> FileStorage[Any]:
    global _default_storage
    if _default_storage is None:
        _default_storage = FileStorage()
    return _default_storage


class StorageQuark(Quark[T]):
    """Quark that persists its value to storage."""

    __slots__ = ("_storage", "_key")

    def __init__(
        self,
        key: str,
        default: T,
        storage: Optional[Storage[T]] = None,
    ) -> None:
        self._storage: Storage[T] = storage or get_default_storage()
        self._key = key
        initial = self._storage.get(key, default)
        super().__init__(initial)

    def set_sync(self, new_value: T) -> None:
        super().set_sync(new_value)
        self._storage.set(self._key, new_value)

    async def set(self, new_value: T) -> None:
        await super().set(new_value)
        self._storage.set(self._key, new_value)


def quark_with_storage(
    key: str,
    default: T,
    storage: Optional[Storage[T]] = None,
) -> StorageQuark[T]:
    """Create a Quark that persists to storage."""
    return StorageQuark(key, default, storage)
