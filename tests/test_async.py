"""Async functionality tests."""

import asyncio

import pytest

from statequark import quark


@pytest.mark.asyncio
async def test_async_set():
    temp = quark(20.0)
    await temp.set(25.5)
    assert temp.value == 25.5


@pytest.mark.asyncio
async def test_async_with_subscriptions():
    values = []
    sensor = quark(10)
    sensor.subscribe(lambda q: values.append(q.value))

    await sensor.set(20)
    await sensor.set(30)

    assert values == [20, 30]


@pytest.mark.asyncio
async def test_derived_cannot_be_set_async():
    base = quark(5)
    derived = quark(lambda get: get(base) * 2, deps=[base])

    with pytest.raises(ValueError):
        await derived.set(10)


@pytest.mark.asyncio
async def test_async_propagates_to_derived():
    base = quark(10)
    values = []

    derived = quark(lambda get: get(base) * 2, deps=[base])
    derived.subscribe(lambda q: values.append(q.value))

    await base.set(15)
    await base.set(20)

    assert values == [30, 40]


@pytest.mark.asyncio
async def test_concurrent_updates():
    counter = quark(0)

    async def increment():
        await asyncio.sleep(0.01)
        await counter.set(counter.value + 1)

    await asyncio.gather(*[increment() for _ in range(5)])
    assert counter.value >= 1


@pytest.mark.asyncio
async def test_async_error_in_callback():
    sensor = quark(0)
    values = []

    sensor.subscribe(lambda q: values.append(q.value))
    sensor.subscribe(lambda q: (_ for _ in ()).throw(Exception("error")))

    await sensor.set(1)
    await sensor.set(2)

    assert values == [1, 2]
