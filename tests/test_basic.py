"""Basic quark functionality tests."""

from statequark import quark


def test_create_quark_with_initial_value():
    """Test creating a quark with an initial value."""
    counter = quark(0)
    assert counter.value == 0

    temperature = quark(20.5)
    assert temperature.value == 20.5

    message = quark("hello")
    assert message.value == "hello"


def test_set_sync():
    """Test synchronous value setting."""
    counter = quark(0)
    counter.set_sync(1)
    assert counter.value == 1

    counter.set_sync(42)
    assert counter.value == 42


def test_different_data_types():
    """Test quarks with different data types."""
    # String
    name = quark("test")
    assert name.value == "test"
    name.set_sync("updated")
    assert name.value == "updated"

    # List
    items = quark([1, 2, 3])
    assert items.value == [1, 2, 3]
    items.set_sync([4, 5, 6])
    assert items.value == [4, 5, 6]

    # Dict
    config = quark({"key": "value"})
    assert config.value == {"key": "value"}
    config.set_sync({"new_key": "new_value"})
    assert config.value == {"new_key": "new_value"}

    # Boolean
    flag = quark(True)
    assert flag.value is True
    flag.set_sync(False)
    assert flag.value is False


def test_quark_repr():
    """Test string representation of quarks."""
    q = quark(42)
    assert repr(q) == "Quark(value=42)"

    q.set_sync("hello")
    assert repr(q) == "Quark(value='hello')"

    q.set_sync([1, 2, 3])
    assert repr(q) == "Quark(value=[1, 2, 3])"


def test_value_property_is_readonly():
    """Test that value property returns current value."""
    counter = quark(10)
    assert counter.value == 10

    # Value should update when we set new value
    counter.set_sync(20)
    assert counter.value == 20
