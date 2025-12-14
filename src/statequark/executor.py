"""Thread pool executor management for StateQuark."""

import atexit
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from .config import get_config
from .logger import log_debug, log_warning


class ExecutorManager:
    """Singleton manager for shared thread pool executor."""

    _instance: Optional["ExecutorManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "ExecutorManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._executor: ThreadPoolExecutor | None = None
        self._executor_lock = threading.Lock()
        self._shutdown = False
        self._initialized: bool = True

        if get_config().auto_cleanup:
            atexit.register(self.cleanup)

        log_debug("ExecutorManager initialized")

    def get_executor(self) -> ThreadPoolExecutor:
        """Get the shared executor, creating if needed."""
        if self._shutdown:
            raise RuntimeError("ExecutorManager has been shut down")

        if self._executor is None:
            with self._executor_lock:
                if self._executor is None:
                    config = get_config()
                    self._executor = ThreadPoolExecutor(
                        max_workers=config.max_workers,
                        thread_name_prefix=config.thread_name_prefix,
                    )
                    log_debug("Thread pool created: %d workers", config.max_workers)

        return self._executor

    def cleanup(self) -> None:
        """Shutdown the executor gracefully."""
        if self._shutdown:
            return

        with self._executor_lock:
            if self._executor is not None and not self._shutdown:
                log_debug("Shutting down executor")
                try:
                    self._executor.shutdown(wait=True, cancel_futures=False)
                except Exception as e:
                    log_warning("Executor shutdown error: %s", e)
                finally:
                    self._executor = None
                    self._shutdown = True

    def reset(self) -> None:
        """Reset for testing purposes."""
        self.cleanup()
        with self._executor_lock:
            self._shutdown = False


_executor_manager: ExecutorManager | None = None
_manager_lock = threading.Lock()


def get_executor_manager() -> ExecutorManager:
    """Get the global executor manager."""
    global _executor_manager
    if _executor_manager is None:
        with _manager_lock:
            if _executor_manager is None:
                _executor_manager = ExecutorManager()
    return _executor_manager


def get_shared_executor() -> ThreadPoolExecutor:
    """Get the shared thread pool executor."""
    return get_executor_manager().get_executor()


def cleanup_executor() -> None:
    """Cleanup the shared executor."""
    get_executor_manager().cleanup()
