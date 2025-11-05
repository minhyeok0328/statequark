"""
Thread pool executor management for StateQuark.

This module manages a shared thread pool for executing callbacks efficiently
in resource-constrained IoT and embedded systems.
"""

import atexit
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from .config import get_config
from .logger import log_debug, log_warning


class ExecutorManager:
    """
    Manages the shared thread pool executor for StateQuark.

    This class follows the singleton pattern to ensure only one thread pool
    exists across the application, minimizing resource usage on embedded systems.
    """

    _instance: Optional["ExecutorManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "ExecutorManager":
        """Create or return the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the executor manager."""
        # Use hasattr to avoid mypy errors with dynamic attributes
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._executor: Optional[ThreadPoolExecutor] = None
        self._executor_lock = threading.Lock()
        self._shutdown = False
        self._initialized: bool = True

        # Register cleanup on exit
        config = get_config()
        if config.auto_cleanup:
            atexit.register(self.cleanup)

        log_debug("ExecutorManager initialized")

    def get_executor(self) -> ThreadPoolExecutor:
        """
        Get the shared thread pool executor.

        Creates the executor if it doesn't exist. The executor is created
        lazily to avoid allocating resources until actually needed.

        Returns:
            ThreadPoolExecutor: The shared thread pool executor.

        Raises:
            RuntimeError: If the executor has been shut down.
        """
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
                    log_debug("Created thread pool with %d workers", config.max_workers)

        return self._executor

    def cleanup(self) -> None:
        """
        Clean up the thread pool executor.

        This method shuts down the executor gracefully, waiting for all
        pending tasks to complete. It's automatically called on application
        exit if auto_cleanup is enabled.
        """
        if self._shutdown:
            return

        with self._executor_lock:
            if self._executor is not None and not self._shutdown:
                log_debug("Shutting down thread pool executor")
                try:
                    self._executor.shutdown(wait=True, cancel_futures=False)
                    log_debug("Thread pool executor shut down successfully")
                except Exception as e:
                    log_warning("Error during executor shutdown: %s", str(e))
                finally:
                    self._executor = None
                    self._shutdown = True

    def reset(self) -> None:
        """
        Reset the executor manager.

        This method is primarily for testing purposes. It shuts down the
        current executor and allows a new one to be created.
        """
        self.cleanup()
        with self._executor_lock:
            self._shutdown = False
            log_debug("ExecutorManager reset")


# Global instance
_executor_manager: Optional[ExecutorManager] = None
_manager_lock = threading.Lock()


def get_executor_manager() -> ExecutorManager:
    """
    Get the global executor manager instance.

    Returns:
        ExecutorManager: The global executor manager.
    """
    global _executor_manager
    if _executor_manager is None:
        with _manager_lock:
            if _executor_manager is None:
                _executor_manager = ExecutorManager()
    return _executor_manager


def get_shared_executor() -> ThreadPoolExecutor:
    """
    Get the shared thread pool executor.

    This is a convenience function that gets the executor from the
    global executor manager.

    Returns:
        ThreadPoolExecutor: The shared thread pool executor.
    """
    return get_executor_manager().get_executor()


def cleanup_executor() -> None:
    """
    Clean up the shared thread pool executor.

    This is a convenience function that calls cleanup on the
    global executor manager.
    """
    manager = get_executor_manager()
    manager.cleanup()
