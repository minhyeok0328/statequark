"""Tests for quark family utilities."""

from statequark import quark, quark_family


class TestQuarkFamily:
    def test_create_and_cache(self):
        sensors = quark_family(lambda id: quark(0.0))

        s1 = sensors("living_room")
        s2 = sensors("bedroom")
        s1_again = sensors("living_room")

        assert s1 is s1_again
        assert s1 is not s2
        assert sensors.size == 2

    def test_remove(self):
        sensors = quark_family(lambda id: quark(0.0))
        sensors("a")
        sensors("b")

        assert sensors.size == 2
        sensors.remove("a")
        assert sensors.size == 1
        assert not sensors.has("a")
        assert sensors.has("b")

    def test_clear(self):
        sensors = quark_family(lambda id: quark(0.0))
        sensors("a")
        sensors("b")
        sensors.clear()

        assert sensors.size == 0

    def test_keys(self):
        sensors = quark_family(lambda id: quark(0.0))
        sensors("x")
        sensors("y")

        assert set(sensors.keys()) == {"x", "y"}
