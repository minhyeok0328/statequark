"""Tests for StateQuark utilities."""

import tempfile
import time

import pytest

from statequark import (
    ValidationError,
    clamp,
    debounce,
    history,
    in_range,
    loadable,
    middleware,
    persist,
    quark,
    quark_family,
    quark_with_reducer,
    quark_with_storage,
    select,
    throttle,
    validate,
)
from statequark.utils.storage import FileStorage, MemoryStorage


class TestQuarkWithStorage:
    def test_memory_storage(self):
        storage = MemoryStorage()
        q = quark_with_storage("test", 10, storage)
        assert q.value == 10

        q.set_sync(20)
        assert q.value == 20
        assert storage.get("test", 0) == 20

    def test_file_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileStorage(tmpdir)
            q = quark_with_storage("sensor", 25.0, storage)
            q.set_sync(30.0)

            # New quark should load persisted value
            q2 = quark_with_storage("sensor", 0.0, storage)
            assert q2.value == 30.0

    def test_storage_with_dict(self):
        storage = MemoryStorage()
        q = quark_with_storage("config", {"threshold": 25}, storage)
        q.set_sync({"threshold": 30, "enabled": True})

        assert storage.get("config", {})["threshold"] == 30


class TestQuarkWithReducer:
    def test_basic_reducer(self):
        def counter_reducer(state, action):
            if action == "INC":
                return state + 1
            if action == "DEC":
                return state - 1
            return state

        counter = quark_with_reducer(0, counter_reducer)
        assert counter.value == 0

        counter.dispatch("INC")
        assert counter.value == 1

        counter.dispatch("INC")
        counter.dispatch("INC")
        assert counter.value == 3

        counter.dispatch("DEC")
        assert counter.value == 2

    def test_reducer_with_dict_action(self):
        def motor_reducer(state, action):
            match action["type"]:
                case "START":
                    return {**state, "running": True}
                case "STOP":
                    return {**state, "running": False}
                case "SET_SPEED":
                    return {**state, "speed": action["value"]}
            return state

        motor = quark_with_reducer({"running": False, "speed": 0}, motor_reducer)
        motor.dispatch({"type": "START"})
        assert motor.value["running"] is True

        motor.dispatch({"type": "SET_SPEED", "value": 100})
        assert motor.value["speed"] == 100

    def test_reducer_subscription(self):
        changes = []

        def reducer(s, a):
            return s + a

        q = quark_with_reducer(0, reducer)
        q.subscribe(lambda x: changes.append(x.value))

        q.dispatch(5)
        q.dispatch(3)
        assert changes == [5, 8]


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

        # Change humidity only - should not trigger
        sensor.set_sync({"temp": 25.0, "humidity": 70})
        assert len(changes) == 0

        # Change temp - should trigger
        sensor.set_sync({"temp": 26.0, "humidity": 70})
        assert changes == [26.0]

    def test_select_cannot_be_set(self):
        source = quark(10)
        doubled = select(source, lambda x: x * 2)

        with pytest.raises(ValueError):
            doubled.set_sync(100)

    def test_select_cleanup(self):
        source = quark(10)
        sel = select(source, lambda x: x * 2)
        sel.cleanup()
        # Should not raise after cleanup


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


class TestDebounce:
    def test_debounce_delays_update(self):
        q = debounce(0, 0.05)
        q.set_sync(1)
        q.set_sync(2)
        q.set_sync(3)

        # Value shouldn't update immediately
        assert q.value == 0

        time.sleep(0.1)
        assert q.value == 3

    def test_debounce_flush_now(self):
        q = debounce(0, 1.0)
        q.set_sync(42)
        q.flush_now()

        assert q.value == 42

    def test_debounce_subscription(self):
        changes = []
        q = debounce(0, 0.05)
        q.subscribe(lambda x: changes.append(x.value))

        q.set_sync(1)
        q.set_sync(2)
        q.set_sync(3)

        time.sleep(0.1)
        assert changes == [3]


class TestThrottle:
    def test_throttle_limits_rate(self):
        q = throttle(0, 0.1)
        q.set_sync(1)  # Should update
        q.set_sync(2)  # Should be ignored
        q.set_sync(3)  # Should be ignored

        assert q.value == 1

        time.sleep(0.15)
        q.set_sync(4)  # Should update
        assert q.value == 4

    def test_throttle_force_set(self):
        q = throttle(0, 1.0)
        q.set_sync(1)
        q.force_set(99)

        assert q.value == 99


class TestHistory:
    def test_undo_redo(self):
        q = history(0)
        q.set_sync(1)
        q.set_sync(2)
        q.set_sync(3)

        assert q.value == 3
        assert q.undo()
        assert q.value == 2
        assert q.undo()
        assert q.value == 1
        assert q.redo()
        assert q.value == 2

    def test_undo_at_start(self):
        q = history(0)
        assert not q.undo()
        assert q.value == 0

    def test_redo_at_end(self):
        q = history(0)
        q.set_sync(1)
        assert not q.redo()

    def test_history_truncation(self):
        q = history(0)
        q.set_sync(1)
        q.set_sync(2)
        q.undo()
        q.set_sync(3)
        assert not q.redo()
        assert q.value == 3

    def test_max_size(self):
        q = history(0, max_size=3)
        for i in range(1, 10):
            q.set_sync(i)
        assert q.history_size <= 4


class TestValidate:
    def test_valid_value(self):
        q = validate(50, in_range(0, 100))
        q.set_sync(75)
        assert q.value == 75

    def test_invalid_raises(self):
        q = validate(50, in_range(0, 100))
        with pytest.raises(ValidationError):
            q.set_sync(150)

    def test_clamp_on_invalid(self):
        q = validate(50, in_range(0, 100), clamp(0, 100))
        q.set_sync(150)
        assert q.value == 100
        q.set_sync(-10)
        assert q.value == 0

    def test_invalid_initial_raises(self):
        with pytest.raises(ValidationError):
            validate(150, in_range(0, 100))


class TestMiddleware:
    def test_basic_middleware(self):
        log = []
        q = middleware(0)
        q.use(lambda old, new, next: (log.append((old, new)), next(new)))

        q.set_sync(1)
        q.set_sync(2)
        assert log == [(0, 1), (1, 2)]

    def test_middleware_chain(self):
        q = middleware(0)
        q.use(lambda o, n, next: next(n * 2))
        q.use(lambda o, n, next: next(n + 1))

        q.set_sync(5)
        assert q.value == 11  # (5 * 2) + 1

    def test_persist_middleware(self):
        storage = {}
        q = middleware(0)
        q.use(persist(storage, "count"))

        q.set_sync(42)
        assert storage["count"] == 42
