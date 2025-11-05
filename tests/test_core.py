"""
Core functionality tests for StateQuark.

This file contains essential smoke tests and backwards compatibility tests.
Comprehensive tests are organized in separate files:
- test_basic.py: Basic quark functionality
- test_derived.py: Derived quark tests
- test_subscriptions.py: Subscription tests
- test_async.py: Async functionality tests
- test_concurrency.py: Thread safety tests
- test_integration.py: Complex integration scenarios
"""

import pytest

from statequark import quark


def test_basic_quark():
    """Basic quark creation and value setting."""
    count = quark(0)
    assert count.value == 0
    count.set_sync(1)
    assert count.value == 1


def test_derived_quark():
    """Basic derived quark functionality."""
    base = quark(2)

    def double_getter(get):
        return get(base) * 2

    double = quark(double_getter, deps=[base])
    assert double.value == 4
    base.set_sync(3)
    assert double.value == 6


@pytest.mark.asyncio
async def test_async_set():
    """Basic async functionality."""
    temperature = quark(20.0)
    await temperature.set(25.5)
    assert temperature.value == 25.5


def test_subscriptions():
    """Basic subscription functionality."""
    values = []
    counter = quark(0)

    def callback(q):
        values.append(q.value)

    counter.subscribe(callback)
    counter.set_sync(1)
    counter.set_sync(2)

    assert values == [1, 2]


def test_import_compatibility():
    """Test that public API is importable."""
    from statequark import Quark, __version__, quark

    # Basic usage should work
    q = quark(42)
    assert isinstance(q, Quark)
    assert q.value == 42

    # Version should be defined
    assert isinstance(__version__, str)
