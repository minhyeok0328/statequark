"""Tests for new features: reset() and batch()."""

import pytest

from statequark import Quark, batch, quark


def test_reset_basic():
    temp = quark(20.0)
    temp.set_sync(99.9)
    assert temp.value == 99.9
    temp.reset()
    assert temp.value == 20.0


def test_reset_with_string():
    name = quark("default")
    name.set_sync("changed")
    name.reset()
    assert name.value == "default"


def test_reset_derived_raises():
    base = quark(10)
    derived = quark(lambda get: get(base) * 2, deps=[base])
    with pytest.raises(ValueError):
        derived.reset()


def test_batch_reduces_notifications():
    call_count = 0

    def counter(q: Quark[int]) -> None:
        nonlocal call_count
        call_count += 1

    a = quark(0)
    b = quark(0)
    a.subscribe(counter)
    b.subscribe(counter)

    with batch():
        a.set_sync(1)
        a.set_sync(2)
        a.set_sync(3)
        b.set_sync(10)

    assert a.value == 3
    assert b.value == 10
    assert call_count == 2  # Once per quark, not per set


def test_batch_with_derived():
    base1 = quark(1)
    base2 = quark(2)
    derived = quark(lambda get: get(base1) + get(base2), deps=[base1, base2])

    notifications = []

    def track(q: Quark[int]) -> None:
        notifications.append(q.value)

    derived.subscribe(track)

    with batch():
        base1.set_sync(10)
        base2.set_sync(20)

    assert derived.value == 30
    # Derived notified per dependency change (base1, base2)
    assert len(notifications) == 2
    assert notifications[-1] == 30


def test_batch_empty():
    with batch():
        pass  # No error


def test_batch_exception_still_notifies():
    notified = []

    def track(q: Quark[int]) -> None:
        notified.append(q.value)

    a = quark(0)
    a.subscribe(track)

    try:
        with batch():
            a.set_sync(5)
            raise RuntimeError("test error")
    except RuntimeError:
        pass

    assert a.value == 5
    assert notified == [5]  # Still notified after exception
