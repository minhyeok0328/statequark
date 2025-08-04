import asyncio
from typing import Any, Callable, Generic, TypeVar, List, Optional
from concurrent.futures import ThreadPoolExecutor
import threading

T = TypeVar("T")
QuarkCallback = Callable[["Quark[Any]"], None]

class Quark(Generic[T]):
    __slots__ = ("_value", "_callbacks", "_executor", "_lock", "_getter", "_deps")

    def __init__(self, initial_or_getter: Any, deps: Optional[List["Quark"]] = None):
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._lock = threading.RLock()
        self._callbacks: List[QuarkCallback] = []
        self._deps = deps or []
        if callable(initial_or_getter):
            self._getter = initial_or_getter
            self._value = self._compute()
            for dep in self._deps:
                dep.subscribe(self._on_dep_change)
        else:
            self._getter = None
            self._value = initial_or_getter

    @property
    def value(self) -> T:
        with self._lock:
            if self._getter:
                return self._compute()
            return self._value

    async def set(self, new_value: T) -> None:
        with self._lock:
            if self._getter:
                raise ValueError("Cannot set derived quark directly")
            self._value = new_value
        await self._notify()

    def set_sync(self, new_value: T) -> None:
        with self._lock:
            if self._getter:
                raise ValueError("Cannot set derived quark directly")
            self._value = new_value
        self._notify_sync()

    def subscribe(self, callback: QuarkCallback) -> None:
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def unsubscribe(self, callback: QuarkCallback) -> None:
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    async def _notify(self) -> None:
        with self._lock:
            callbacks_copy = self._callbacks[:]
        if not callbacks_copy:
            return
        await asyncio.gather(
            *[asyncio.get_event_loop().run_in_executor(self._executor, self._safe_call, cb)
              for cb in callbacks_copy]
        )

    def _notify_sync(self) -> None:
        with self._lock:
            callbacks_copy = self._callbacks[:]
        for cb in callbacks_copy:
            self._safe_call(cb)

    def _safe_call(self, callback: QuarkCallback) -> None:
        try:
            callback(self)
        except Exception as e:
            print(f"Callback error: {e}")

    def _compute(self) -> T:
        def get(dep_quark: "Quark") -> Any:
            return dep_quark.value
        if self._getter is None:
            raise ValueError("Cannot compute value for non-derived quark")
        return self._getter(get)

    def _on_dep_change(self, dep: "Quark") -> None:
        self._notify_sync()

    def __repr__(self) -> str:
        return f"Quark(value={self.value!r})"

def quark(initial_or_getter: Any, deps: Optional[List[Quark]] = None) -> Quark:
    return Quark(initial_or_getter, deps)