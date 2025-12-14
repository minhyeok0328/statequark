"""Configuration tests."""

import threading

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
    reset_config()
    config = get_config()

    assert config.debug is False
    assert config.max_workers == 4
    assert config.auto_cleanup is True


def test_enable_disable_debug():
    reset_config()

    assert is_debug_enabled() is False
    enable_debug()
    assert is_debug_enabled() is True
    disable_debug()
    assert is_debug_enabled() is False


def test_custom_config():
    set_config(StateQuarkConfig(debug=True, max_workers=2))

    assert get_config().debug is True
    assert get_config().max_workers == 2

    reset_config()


def test_config_validation():
    with pytest.raises(ValueError):
        StateQuarkConfig(max_workers=0)

    with pytest.raises(ValueError):
        StateQuarkConfig(max_workers=64)


def test_context_manager():
    values = []

    with quark(10) as q:
        q.subscribe(lambda q: values.append(q.value))
        q.set(20)
        q.set(30)

    assert values == [20, 30]


def test_config_thread_safety():
    reset_config()
    results = []

    def worker():
        results.append(get_config().max_workers)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(w == 4 for w in results)
