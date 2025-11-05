"""Tests for configuration and logging functionality."""

import pytest

from statequark import (
    StateQuarkConfig,
    disable_debug,
    enable_debug,
    get_config,
    quark,
    reset_config,
    set_config,
)
from statequark.logger import is_debug_enabled


def test_default_config():
    """Test default configuration values."""
    reset_config()
    config = get_config()

    assert config.debug is False
    assert config.max_workers == 4
    assert config.thread_name_prefix == "quark-callback"
    assert config.auto_cleanup is True


def test_enable_disable_debug():
    """Test enabling and disabling debug mode."""
    reset_config()

    # Initially disabled
    assert is_debug_enabled() is False

    # Enable debug
    enable_debug()
    assert is_debug_enabled() is True

    # Disable debug
    disable_debug()
    assert is_debug_enabled() is False


def test_custom_config():
    """Test setting custom configuration."""
    custom_config = StateQuarkConfig(
        debug=True, max_workers=2, thread_name_prefix="custom-thread"
    )

    set_config(custom_config)
    current_config = get_config()

    assert current_config.debug is True
    assert current_config.max_workers == 2
    assert current_config.thread_name_prefix == "custom-thread"

    # Reset to default
    reset_config()


def test_config_validation():
    """Test configuration validation."""
    # Invalid max_workers (too low)
    with pytest.raises(ValueError, match="max_workers must be at least 1"):
        StateQuarkConfig(max_workers=0)

    # Invalid max_workers (too high)
    with pytest.raises(ValueError, match="max_workers should not exceed 32"):
        StateQuarkConfig(max_workers=64)


def test_config_with_quark():
    """Test that configuration affects quark behavior."""
    reset_config()

    # Create quark with debug disabled
    temp = quark(20.0)
    assert temp.value == 20.0

    # Enable debug mode
    enable_debug()
    assert is_debug_enabled() is True

    # Create another quark (should work the same but with logging)
    humidity = quark(50.0)
    assert humidity.value == 50.0

    # Disable debug
    disable_debug()
    assert is_debug_enabled() is False

    # Cleanup
    temp.cleanup()
    humidity.cleanup()


def test_context_manager():
    """Test quark as context manager."""
    values = []

    def callback(q):
        values.append(q.value)

    with quark(10) as q:
        q.subscribe(callback)
        q.set_sync(20)
        q.set_sync(30)

    # After context exit, cleanup should have been called
    assert values == [20, 30]

    # Callbacks should be cleared
    # (though we can't directly test this without accessing internals)


def test_reset_config():
    """Test resetting configuration to defaults."""
    # Set custom config
    custom_config = StateQuarkConfig(debug=True, max_workers=8)
    set_config(custom_config)

    assert get_config().debug is True
    assert get_config().max_workers == 8

    # Reset to defaults
    reset_config()

    assert get_config().debug is False
    assert get_config().max_workers == 4


def test_config_thread_safety():
    """Test that configuration is thread-safe."""
    import threading

    reset_config()
    results = []

    def worker():
        config = get_config()
        results.append(config.max_workers)

    threads = [threading.Thread(target=worker) for _ in range(10)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # All threads should see the same config
    assert all(workers == 4 for workers in results)
    assert len(results) == 10
