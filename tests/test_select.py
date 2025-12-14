"""Tests for select utilities."""

import pytest

from statequark import quark, select


class TestSelect:
    def test_select_field(self):
        sensor = quark({"temp": 25.0, "humidity": 60})
        temp = select(sensor, lambda d: d["temp"])

        assert temp.value == 25.0

    def test_select_only_triggers_on_change(self):
        sensor = quark({"temp": 25.0, "humidity": 60})
        temp = select(sensor, lambda d: d["temp"])

        changes = []
        temp.subscribe(lambda x: changes.append(x.value))

        sensor.set({"temp": 25.0, "humidity": 70})
        assert len(changes) == 0

        sensor.set({"temp": 26.0, "humidity": 70})
        assert changes == [26.0]

    def test_select_cannot_be_set(self):
        source = quark(10)
        doubled = select(source, lambda x: x * 2)

        with pytest.raises(ValueError):
            doubled.set(100)

    def test_select_cleanup(self):
        source = quark(10)
        sel = select(source, lambda x: x * 2)
        sel.cleanup()
