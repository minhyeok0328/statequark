"""Basic quark functionality tests."""

import pytest

from statequark import Quark, __version__, quark


def test_create_with_initial_value():
    assert quark(0).value == 0
    assert quark(20.5).value == 20.5
    assert quark("hello").value == "hello"


def test_set():
    counter = quark(0)
    counter.set(1)
    assert counter.value == 1
    counter.set(42)
    assert counter.value == 42


def test_different_data_types():
    assert quark([1, 2, 3]).value == [1, 2, 3]
    assert quark({"key": "value"}).value == {"key": "value"}
    assert quark(True).value is True


def test_repr():
    assert repr(quark(42)) == "Quark(value=42)"
    assert repr(quark("hello")) == "Quark(value='hello')"


def test_derived_quark():
    base = quark(2)
    double = quark(lambda get: get(base) * 2, deps=[base])
    assert double.value == 4
    base.set(3)
    assert double.value == 6


@pytest.mark.asyncio
async def test_async_set():
    temp = quark(20.0)
    await temp.set_async(25.5)
    assert temp.value == 25.5


def test_subscriptions():
    values = []
    counter = quark(0)
    counter.subscribe(lambda q: values.append(q.value))
    counter.set(1)
    counter.set(2)
    assert values == [1, 2]


def test_import_compatibility():
    q = quark(42)
    assert isinstance(q, Quark)
    assert isinstance(__version__, str)


def test_generic_syntax():
    """Test quark[Type](value) syntax."""
    # Basic generic syntax
    count = quark[int](0)
    assert count.value == 0
    count.set(42)
    assert count.value == 42

    # With None initial value
    name = quark[str | None](None)
    assert name.value is None
    name.set("hello")
    assert name.value == "hello"

    # Complex types
    items = quark[list[str]]([])
    assert items.value == []
    items.set(["a", "b"])
    assert items.value == ["a", "b"]


def test_generic_and_inferred_equivalence():
    """Both syntaxes should produce identical Quark instances."""
    inferred = quark(100)
    explicit = quark[int](100)

    assert type(inferred) == type(explicit)
    assert inferred.value == explicit.value

    inferred.set(200)
    explicit.set(200)
    assert inferred.value == explicit.value
