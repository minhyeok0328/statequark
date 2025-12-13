"""Tests for loadable utilities."""

from statequark import loadable, quark


class TestLoadable:
    def test_initial_has_data(self):
        source = quark(42)
        loaded = loadable(source)

        assert loaded.value.state == "hasData"
        assert loaded.value.data == 42

    def test_set_loading(self):
        source = quark(0)
        loaded = loadable(source)

        loaded.set_loading()
        assert loaded.value.state == "loading"

    def test_set_error(self):
        source = quark(0)
        loaded = loadable(source)

        loaded.set_error(ValueError("test error"))
        assert loaded.value.state == "hasError"
        assert isinstance(loaded.value.error, ValueError)

    def test_source_change_updates_loadable(self):
        source = quark(1)
        loaded = loadable(source)

        source.set_sync(2)
        assert loaded.value.state == "hasData"
        assert loaded.value.data == 2
