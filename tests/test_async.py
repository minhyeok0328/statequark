"""Async functionality tests."""
import pytest
import asyncio
from statequark import quark


@pytest.mark.asyncio
async def test_async_set():
    """Test async value setting."""
    temperature = quark(20.0)
    await temperature.set(25.5)
    assert temperature.value == 25.5
    
    await temperature.set(30.0)
    assert temperature.value == 30.0


@pytest.mark.asyncio
async def test_async_with_subscriptions():
    """Test async updates with subscriptions."""
    values = []
    sensor = quark(10)
    
    def callback(q):
        values.append(q.value)
    
    sensor.subscribe(callback)
    await sensor.set(20)
    await sensor.set(30)
    
    assert values == [20, 30]


@pytest.mark.asyncio
async def test_derived_quark_cannot_be_set_async():
    """Test that derived quarks cannot be set asynchronously."""
    base = quark(5)
    
    def derived_getter(get):
        return get(base) * 2
    
    derived = quark(derived_getter, deps=[base])
    
    with pytest.raises(ValueError, match="Cannot set derived quark directly"):
        await derived.set(10)


@pytest.mark.asyncio
async def test_async_with_derived_quarks():
    """Test async updates propagating to derived quarks."""
    base = quark(10)
    values = []
    
    def double(get):
        return get(base) * 2
    
    def callback(q):
        values.append(q.value)
    
    derived = quark(double, deps=[base])
    derived.subscribe(callback)
    
    await base.set(15)
    await base.set(20)
    
    assert values == [30, 40]


@pytest.mark.asyncio
async def test_concurrent_async_updates():
    """Test concurrent async updates."""
    counter = quark(0)
    
    async def increment():
        current = counter.value
        await asyncio.sleep(0.01)  # Simulate async work
        await counter.set(current + 1)
    
    # Start multiple concurrent increments
    await asyncio.gather(*[increment() for _ in range(10)])
    
    # Note: Due to race conditions, final value may not be 10
    # This tests that async operations complete without error
    assert counter.value >= 1


@pytest.mark.asyncio
async def test_async_callback_execution():
    """Test that callbacks are executed asynchronously."""
    sensor = quark(0)
    execution_order = []
    
    def callback(q):
        execution_order.append(f"callback_{q.value}")
    
    sensor.subscribe(callback)
    
    execution_order.append("before_set")
    await sensor.set(1)
    execution_order.append("after_set")
    
    # Callback should be executed
    assert "callback_1" in execution_order
    

@pytest.mark.asyncio
async def test_async_with_multiple_dependencies():
    """Test async updates with multiple dependencies."""
    temp = quark(20.0)
    humidity = quark(50.0)
    values = []
    
    def comfort_status(get):
        t = get(temp)
        h = get(humidity)
        return f"temp:{t},humidity:{h}"
    
    def callback(q):
        values.append(q.value)
    
    status = quark(comfort_status, deps=[temp, humidity])
    status.subscribe(callback)
    
    await temp.set(25.0)
    await humidity.set(60.0)
    await temp.set(22.0)
    
    expected = ["temp:25.0,humidity:50.0", "temp:25.0,humidity:60.0", "temp:22.0,humidity:60.0"]
    assert values == expected


@pytest.mark.asyncio
async def test_async_error_in_callback():
    """Test async behavior when callback raises error."""
    sensor = quark(0)
    good_values = []
    
    def good_callback(q):
        good_values.append(q.value)
    
    def bad_callback(q):
        raise Exception("Async callback error")
    
    sensor.subscribe(good_callback)
    sensor.subscribe(bad_callback)
    
    await sensor.set(1)
    await sensor.set(2)
    
    # Good callback should still work
    assert good_values == [1, 2]


@pytest.mark.asyncio 
async def test_async_sequence():
    """Test a sequence of async operations."""
    pipeline = quark(0)
    results = []
    
    def stage_callback(q):
        results.append(f"stage_{q.value}")
    
    pipeline.subscribe(stage_callback)
    
    # Simulate a processing pipeline
    await pipeline.set(1)  # Input
    await pipeline.set(2)  # Processing
    await pipeline.set(3)  # Output
    
    assert results == ["stage_1", "stage_2", "stage_3"]


@pytest.mark.asyncio
async def test_async_with_network_simulation():
    """Test async pattern simulating network operations."""
    sensor_data = quark({})
    processed_data = []
    
    def process_data(get):
        data = get(sensor_data)
        if not data:
            return "no_data"
        return f"processed_{data.get('value', 'unknown')}"
    
    def callback(q):
        processed_data.append(q.value)
    
    processor = quark(process_data, deps=[sensor_data])
    processor.subscribe(callback)
    
    # Simulate network data updates
    await sensor_data.set({"value": "temp_25", "timestamp": "12:00"})
    await asyncio.sleep(0.01)  # Simulate network delay
    await sensor_data.set({"value": "temp_30", "timestamp": "12:01"})
    
    assert "processed_temp_25" in processed_data
    assert "processed_temp_30" in processed_data