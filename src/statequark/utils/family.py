"""QuarkFamily for dynamic Quark creation."""

from collections.abc import Callable
from typing import Generic, TypeVar

from ..atom import Quark

K = TypeVar("K")
V = TypeVar("V")


class QuarkFamily(Generic[K, V]):
    """Factory for creating and caching Quarks by key."""

    __slots__ = ("_factory", "_cache", "_equals")

    def __init__(
        self,
        factory: Callable[[K], Quark[V]],
        equals: Callable[[K, K], bool] | None = None,
    ) -> None:
        self._factory = factory
        self._cache: dict[K, Quark[V]] = {}
        self._equals = equals

    def __call__(self, key: K) -> Quark[V]:
        """Get or create a Quark for the given key."""
        if self._equals:
            for k, v in self._cache.items():
                if self._equals(k, key):
                    return v

        if key not in self._cache:
            self._cache[key] = self._factory(key)
        return self._cache[key]

    def has(self, key: K) -> bool:
        """Check if a Quark exists for the key."""
        if self._equals:
            return any(self._equals(k, key) for k in self._cache)
        return key in self._cache

    def remove(self, key: K) -> bool:
        """Remove and cleanup a Quark by key."""
        if self._equals:
            for k in list(self._cache.keys()):
                if self._equals(k, key):
                    self._cache[k].cleanup()
                    del self._cache[k]
                    return True
            return False

        if key in self._cache:
            self._cache[key].cleanup()
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Remove and cleanup all Quarks."""
        for q in self._cache.values():
            q.cleanup()
        self._cache.clear()

    def keys(self) -> list[K]:
        """Get all keys."""
        return list(self._cache.keys())

    @property
    def size(self) -> int:
        """Number of cached Quarks."""
        return len(self._cache)


def quark_family(
    factory: Callable[[K], Quark[V]],
    equals: Callable[[K, K], bool] | None = None,
) -> QuarkFamily[K, V]:
    """Create a QuarkFamily for dynamic Quark management."""
    return QuarkFamily(factory, equals)
