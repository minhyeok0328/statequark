"""
Storage utilities for StateQuark.

Provides persistent storage capabilities for quarks, similar to Jotai's
atomWithStorage. Designed for IoT environments where state needs to persist
across device restarts.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional, Protocol

from .core import Quark, quark
from .logger import log_debug, log_error, log_warning
from .types import T


class StorageType(Enum):
    """Storage type for quark persistence."""

    SESSION = "session"  # Temporary storage in /tmp/statequark/
    LOCAL = "local"  # Persistent storage in ./.statequark/ (configurable)


class Storage(Protocol):
    """Protocol for storage backends."""

    def get_item(self, key: str) -> Optional[str]:
        """Get an item from storage."""
        ...

    def set_item(self, key: str, value: str) -> None:
        """Set an item in storage."""
        ...

    def remove_item(self, key: str) -> None:
        """Remove an item from storage."""
        ...


class FileStorage:
    """
    File-based storage implementation for quarks.

    Stores values as JSON files in the filesystem, providing persistent
    storage for IoT devices.

    Args:
        storage_type: Type of storage (SESSION or LOCAL).
        base_path: Base directory for LOCAL storage. Defaults to current directory.

    Example:
        >>> storage = FileStorage(StorageType.LOCAL)
        >>> storage.set_item("temperature", "25.5")
        >>> storage.get_item("temperature")
        '25.5'
    """

    def __init__(
        self,
        storage_type: StorageType = StorageType.LOCAL,
        base_path: Optional[str] = None,
    ) -> None:
        """
        Initialize file storage.

        Args:
            storage_type: Type of storage (SESSION or LOCAL).
            base_path: Custom base path for LOCAL storage.
        """
        self.storage_type = storage_type

        if storage_type == StorageType.SESSION:
            # Session storage in /tmp/statequark/
            self.storage_dir = Path("/tmp/statequark")
        else:
            # Local storage in ./.statequark/ or custom path
            if base_path:
                self.storage_dir = Path(base_path) / ".statequark"
            else:
                self.storage_dir = Path.cwd() / ".statequark"

        # Create storage directory if it doesn't exist
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            log_debug(
                "FileStorage initialized: type=%s, path=%s",
                storage_type.value,
                self.storage_dir,
            )
        except Exception as e:
            log_error("Failed to create storage directory %s: %s", self.storage_dir, e)
            raise

    def _get_file_path(self, key: str) -> Path:
        """Get the file path for a storage key."""
        # Sanitize key to make it filesystem-safe
        safe_key = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in key)
        return self.storage_dir / f"{safe_key}.json"

    def get_item(self, key: str) -> Optional[str]:
        """
        Get an item from storage.

        Args:
            key: Storage key.

        Returns:
            Stored value as string, or None if not found.
        """
        file_path = self._get_file_path(key)

        try:
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    value = f.read()
                    log_debug("FileStorage.get_item: key=%s, found", key)
                    return value
            else:
                log_debug("FileStorage.get_item: key=%s, not found", key)
                return None
        except Exception as e:
            log_error("FileStorage.get_item failed for key=%s: %s", key, e)
            return None

    def set_item(self, key: str, value: str) -> None:
        """
        Set an item in storage.

        Args:
            key: Storage key.
            value: Value to store as string.
        """
        file_path = self._get_file_path(key)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(value)
            log_debug("FileStorage.set_item: key=%s, value=%s", key, value)
        except Exception as e:
            log_error("FileStorage.set_item failed for key=%s: %s", key, e)
            raise

    def remove_item(self, key: str) -> None:
        """
        Remove an item from storage.

        Args:
            key: Storage key.
        """
        file_path = self._get_file_path(key)

        try:
            if file_path.exists():
                file_path.unlink()
                log_debug("FileStorage.remove_item: key=%s", key)
            else:
                log_debug("FileStorage.remove_item: key=%s not found", key)
        except Exception as e:
            log_warning("FileStorage.remove_item failed for key=%s: %s", key, e)


def quark_with_storage(
    key: str,
    initial_value: T,
    storage_type: StorageType = StorageType.LOCAL,
    base_path: Optional[str] = None,
) -> Quark[T]:
    """
    Create a quark with persistent storage.

    Similar to Jotai's atomWithStorage, this creates a quark that automatically
    persists its value to the filesystem. Perfect for IoT devices that need to
    maintain state across reboots.

    Args:
        key: Unique storage key for this quark.
        initial_value: Default value if no stored value exists.
        storage_type: Type of storage (SESSION or LOCAL).
        base_path: Custom base path for LOCAL storage.

    Returns:
        Quark instance with storage persistence.

    Example:
        >>> # Session storage (temporary, in /tmp/statequark/)
        >>> temp_sensor = quark_with_storage(
        ...     "temperature",
        ...     20.0,
        ...     StorageType.SESSION
        ... )

        >>> # Local storage (persistent, in ./.statequark/)
        >>> humidity_sensor = quark_with_storage(
        ...     "humidity",
        ...     50.0,
        ...     StorageType.LOCAL
        ... )

        >>> # Custom storage path
        >>> pressure_sensor = quark_with_storage(
        ...     "pressure",
        ...     1013.25,
        ...     StorageType.LOCAL,
        ...     base_path="/var/lib/myapp"
        ... )

        >>> # Value persists across program restarts
        >>> temp_sensor.set(25.5)
        >>> # ... program restarts ...
        >>> temp_sensor = quark_with_storage("temperature", 20.0, StorageType.SESSION)
        >>> temp_sensor.value  # 25.5 (loaded from storage)
    """
    storage = FileStorage(storage_type, base_path)

    # Try to load existing value from storage
    try:
        stored_value = storage.get_item(key)
        if stored_value is not None:
            # Deserialize the stored value
            value = json.loads(stored_value)
            log_debug(
                "quark_with_storage: loaded %s=%r from storage",
                key,
                value,
            )
        else:
            # Use initial value and save it
            value = initial_value
            storage.set_item(key, json.dumps(value))
            log_debug(
                "quark_with_storage: initialized %s=%r",
                key,
                value,
            )
    except Exception as e:
        log_error(
            "quark_with_storage: failed to load %s, using initial value: %s",
            key,
            e,
        )
        value = initial_value

    # Create the quark
    q = quark(value)

    # Override the set method to also persist to storage
    original_set = q.set

    def set_with_storage(new_value: T) -> None:
        """Set value and persist to storage."""
        try:
            # Update storage
            storage.set_item(key, json.dumps(new_value))
            log_debug("quark_with_storage: persisted %s=%r", key, new_value)
        except Exception as e:
            log_error("quark_with_storage: failed to persist %s: %s", key, e)

        # Update quark value
        original_set(new_value)

    # Replace the set method
    q.set = set_with_storage  # type: ignore

    return q


def quark_with_reset(initial_value: T) -> tuple[Quark[T], Quark[None]]:
    """
    Create a quark with a reset capability.

    Returns a tuple of (value_quark, reset_quark). Setting any value on
    reset_quark will reset value_quark to its initial value.

    Useful for IoT devices that need a "factory reset" capability.

    Args:
        initial_value: The default value to reset to.

    Returns:
        Tuple of (value quark, reset quark).

    Example:
        >>> sensor_value, reset_sensor = quark_with_reset(20.0)
        >>> sensor_value.set(25.5)
        >>> sensor_value.value
        25.5
        >>> reset_sensor.set(None)  # Reset to initial value
        >>> sensor_value.value
        20.0
    """
    value_quark = quark(initial_value)
    reset_quark = quark(None)

    def on_reset(q: Quark[None]) -> None:
        """Reset the value quark when reset quark changes."""
        value_quark.set(initial_value)
        log_debug("quark_with_reset: reset to %r", initial_value)

    reset_quark.subscribe(on_reset)

    return value_quark, reset_quark


def quark_with_default(
    get_default: Callable[[Callable[[Quark[Any]], Any]], T],
    deps: list[Quark[Any]],
    fallback: T,
) -> Quark[T]:
    """
    Create a derived quark with a fallback value.

    If the getter function raises an exception, the fallback value is used.
    Useful for sensor readings that may fail.

    Args:
        get_default: Getter function that may raise exceptions.
        deps: Dependencies for the derived quark.
        fallback: Value to use if getter fails.

    Returns:
        Derived quark with fallback.

    Example:
        >>> sensor = quark(None)  # May be None if sensor disconnected
        >>> def get_value(get):
        ...     val = get(sensor)
        ...     if val is None:
        ...         raise ValueError("Sensor disconnected")
        ...     return val
        >>> safe_sensor = quark_with_default(get_value, [sensor], 0.0)
        >>> safe_sensor.value  # 0.0 (fallback when sensor is None)
    """

    def safe_getter(get: Callable[[Quark[Any]], Any]) -> T:
        """Getter with exception handling."""
        try:
            return get_default(get)
        except Exception as e:
            log_warning("quark_with_default: using fallback due to error: %s", e)
            return fallback

    return quark(safe_getter, deps=deps)
