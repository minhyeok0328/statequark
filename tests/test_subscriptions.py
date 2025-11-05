"""Subscription and callback functionality tests."""

from statequark import quark


def test_basic_subscription():
    """Test basic subscription functionality."""
    values = []
    counter = quark(0)

    def callback(q):
        values.append(q.value)

    counter.subscribe(callback)
    counter.set_sync(1)
    counter.set_sync(2)
    counter.set_sync(3)

    assert values == [1, 2, 3]


def test_unsubscribe():
    """Test unsubscribing from callbacks."""
    values = []
    counter = quark(0)

    def callback(q):
        values.append(q.value)

    counter.subscribe(callback)
    counter.set_sync(1)

    counter.unsubscribe(callback)
    counter.set_sync(2)

    assert values == [1]


def test_multiple_subscribers():
    """Test multiple subscribers on the same quark."""
    values1 = []
    values2 = []
    counter = quark(0)

    def callback1(q):
        values1.append(q.value)

    def callback2(q):
        values2.append(q.value * 2)

    counter.subscribe(callback1)
    counter.subscribe(callback2)
    counter.set_sync(5)

    assert values1 == [5]
    assert values2 == [10]


def test_callback_with_derived_quark():
    """Test subscriptions on derived quarks."""
    base = quark(10)
    values = []

    def double(get):
        return get(base) * 2

    def callback(q):
        values.append(q.value)

    derived = quark(double, deps=[base])
    derived.subscribe(callback)

    # Changes to base should trigger derived callbacks
    base.set_sync(15)
    base.set_sync(20)

    assert values == [30, 40]


def test_callback_error_handling():
    """Test that callback errors don't break other callbacks."""
    counter = quark(0)
    values = []

    def good_callback(q):
        values.append(q.value)

    def bad_callback(q):
        raise Exception("Test error")

    def another_good_callback(q):
        values.append(q.value * 2)

    counter.subscribe(good_callback)
    counter.subscribe(bad_callback)
    counter.subscribe(another_good_callback)

    counter.set_sync(5)

    # Good callbacks should still work despite bad callback
    assert values == [5, 10]


def test_subscription_with_complex_callback():
    """Test subscriptions with more complex callback logic."""
    temperature = quark(20.0)
    alerts = []

    def temperature_monitor(q):
        temp = q.value
        if temp > 30:
            alerts.append(f"HIGH: {temp}°C")
        elif temp < 10:
            alerts.append(f"LOW: {temp}°C")
        else:
            alerts.append(f"NORMAL: {temp}°C")

    temperature.subscribe(temperature_monitor)

    temperature.set_sync(25.0)
    temperature.set_sync(35.0)
    temperature.set_sync(5.0)

    assert alerts == ["NORMAL: 25.0°C", "HIGH: 35.0°C", "LOW: 5.0°C"]


def test_no_callback_on_initial_value():
    """Test that callbacks are not triggered on initial value."""
    values = []

    def callback(q):
        values.append(q.value)

    # Create quark with initial value
    counter = quark(42)

    # Subscribe after creation
    counter.subscribe(callback)

    # Should be empty - no callback on initial value
    assert values == []

    # But should trigger on actual changes
    counter.set_sync(43)
    assert values == [43]


def test_unsubscribe_nonexistent_callback():
    """Test unsubscribing a callback that was never subscribed."""
    counter = quark(0)

    def callback(q):
        pass

    # Should not raise an error
    counter.unsubscribe(callback)

    # Subscribe then unsubscribe twice
    counter.subscribe(callback)
    counter.unsubscribe(callback)
    counter.unsubscribe(callback)  # Should not error


def test_subscribe_same_callback_twice():
    """Test subscribing the same callback multiple times."""
    values = []
    counter = quark(0)

    def callback(q):
        values.append(q.value)

    # Subscribe same callback twice
    counter.subscribe(callback)
    counter.subscribe(callback)

    counter.set_sync(1)

    # Should only be called once (no duplicates)
    assert values == [1]


def test_subscription_chain():
    """Test subscription chains with derived quarks."""
    base = quark(1)
    chain_values = []

    def double(get):
        return get(base) * 2

    def quadruple(get):
        return get(doubled) * 2

    def chain_callback(q):
        chain_values.append(q.value)

    doubled = quark(double, deps=[base])
    quadrupled = quark(quadruple, deps=[doubled])

    # Subscribe to all levels
    base.subscribe(chain_callback)
    doubled.subscribe(chain_callback)
    quadrupled.subscribe(chain_callback)

    base.set_sync(3)

    # Should trigger callbacks for all dependent quarks
    assert 3 in chain_values  # base
    assert 6 in chain_values  # doubled
    assert 12 in chain_values  # quadrupled
