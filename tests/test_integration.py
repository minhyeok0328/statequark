"""Integration tests for real-world scenarios."""

import asyncio

import pytest

from statequark import quark


def test_iot_monitoring_system():
    temperature = quark(22.0)
    humidity = quark(45.0)
    battery = quark(85.0)
    alerts = []

    def status(get):
        if get(battery) < 20:
            return "critical"
        if get(temperature) > 30 or get(humidity) > 80:
            return "warning"
        return "normal"

    system_status = quark(status, deps=[temperature, humidity, battery])
    system_status.subscribe(lambda q: alerts.append(q.value) if q.value != "normal" else None)

    assert system_status.value == "normal"

    temperature.set_sync(35.0)
    assert system_status.value == "warning"
    assert "warning" in alerts

    battery.set_sync(15.0)
    assert system_status.value == "critical"


def test_thermostat_control():
    current = quark(20.0)
    target = quark(22.0)
    commands = []

    heating = quark(lambda get: get(current) < get(target) - 0.5, deps=[current, target])
    heating.subscribe(lambda q: commands.append("on" if q.value else "off"))

    assert heating.value is True

    current.set_sync(18.0)
    assert commands[-1] == "on"

    current.set_sync(22.5)
    assert heating.value is False
    assert commands[-1] == "off"


def test_derived_chain():
    sensor1 = quark(10.0)
    sensor2 = quark(20.0)

    average = quark(lambda get: (get(sensor1) + get(sensor2)) / 2, deps=[sensor1, sensor2])
    status = quark(lambda get: "high" if get(average) > 20 else "normal", deps=[average])

    assert status.value == "normal"

    sensor1.set_sync(30.0)
    assert average.value == 25.0
    assert status.value == "high"


@pytest.mark.asyncio
async def test_async_sensor_network():
    sensors = [quark(0.0) for _ in range(3)]
    total = quark(lambda get: sum(get(s) for s in sensors), deps=sensors)

    await asyncio.gather(*[s.set(i * 10.0) for i, s in enumerate(sensors)])

    assert total.value == 30.0


def test_cleanup_removes_subscriptions():
    base = quark(10)
    derived = quark(lambda get: get(base) * 2, deps=[base])
    updates = []

    derived.subscribe(lambda q: updates.append(q.value))

    base.set_sync(20)
    assert len(updates) == 1

    derived.cleanup()
    base.set_sync(30)
    assert len(updates) == 1  # No updates after cleanup
