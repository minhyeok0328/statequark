"""Tests for timing utilities (debounce, throttle)."""

import time

from statequark import debounce, throttle


class TestDebounce:
    def test_debounce_delays_update(self):
        q = debounce(0, 0.05)
        q.set(1)
        q.set(2)
        q.set(3)

        assert q.value == 0

        time.sleep(0.1)
        assert q.value == 3

    def test_debounce_flush_now(self):
        q = debounce(0, 1.0)
        q.set(42)
        q.flush_now()

        assert q.value == 42

    def test_debounce_subscription(self):
        changes = []
        q = debounce(0, 0.05)
        q.subscribe(lambda x: changes.append(x.value))

        q.set(1)
        q.set(2)
        q.set(3)

        time.sleep(0.1)
        assert changes == [3]


class TestThrottle:
    def test_throttle_limits_rate(self):
        q = throttle(0, 0.1)
        q.set(1)
        q.set(2)
        q.set(3)

        assert q.value == 1

        time.sleep(0.15)
        q.set(4)
        assert q.value == 4

    def test_throttle_force_set(self):
        q = throttle(0, 1.0)
        q.set(1)
        q.force_set(99)

        assert q.value == 99
