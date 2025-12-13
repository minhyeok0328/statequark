"""Derived quark tests."""

import pytest

from statequark import quark


def test_simple_derived():
    base = quark(2)
    double = quark(lambda get: get(base) * 2, deps=[base])

    assert double.value == 4
    base.set_sync(3)
    assert double.value == 6


def test_multiple_dependencies():
    temp = quark(25.0)
    humidity = quark(60.0)

    comfort = quark(
        lambda get: (
            "ok" if 20 <= get(temp) <= 26 and 40 <= get(humidity) <= 70 else "bad"
        ),
        deps=[temp, humidity],
    )

    assert comfort.value == "ok"
    temp.set_sync(30.0)
    assert comfort.value == "bad"


def test_nested_derived():
    base = quark(2)
    doubled = quark(lambda get: get(base) * 2, deps=[base])
    quadrupled = quark(lambda get: get(doubled) * 2, deps=[doubled])

    assert quadrupled.value == 8
    base.set_sync(3)
    assert quadrupled.value == 12


def test_cannot_set_derived():
    base = quark(5)
    derived = quark(lambda get: get(base) * 2, deps=[base])

    with pytest.raises(ValueError):
        derived.set_sync(10)


def test_conditional_logic():
    value = quark(50.0)
    threshold = quark(75.0)

    def status(get):
        v, t = get(value), get(threshold)
        if v > t:
            return "ALARM"
        if v > t * 0.8:
            return "WARNING"
        return "NORMAL"

    alarm = quark(status, deps=[value, threshold])

    assert alarm.value == "NORMAL"
    value.set_sync(65.0)
    assert alarm.value == "WARNING"
    value.set_sync(80.0)
    assert alarm.value == "ALARM"
