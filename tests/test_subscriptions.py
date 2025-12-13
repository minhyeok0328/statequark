"""Subscription tests."""

from statequark import quark


def test_basic_subscription():
    values = []
    counter = quark(0)
    counter.subscribe(lambda q: values.append(q.value))

    counter.set_sync(1)
    counter.set_sync(2)

    assert values == [1, 2]


def test_unsubscribe():
    values = []
    counter = quark(0)
    cb = lambda q: values.append(q.value)

    counter.subscribe(cb)
    counter.set_sync(1)
    counter.unsubscribe(cb)
    counter.set_sync(2)

    assert values == [1]


def test_multiple_subscribers():
    v1, v2 = [], []
    counter = quark(0)

    counter.subscribe(lambda q: v1.append(q.value))
    counter.subscribe(lambda q: v2.append(q.value * 2))
    counter.set_sync(5)

    assert v1 == [5]
    assert v2 == [10]


def test_derived_subscription():
    base = quark(10)
    values = []

    derived = quark(lambda get: get(base) * 2, deps=[base])
    derived.subscribe(lambda q: values.append(q.value))

    base.set_sync(15)
    base.set_sync(20)

    assert values == [30, 40]


def test_error_in_callback():
    counter = quark(0)
    values = []

    counter.subscribe(lambda q: values.append(q.value))
    counter.subscribe(lambda q: (_ for _ in ()).throw(Exception("error")))
    counter.subscribe(lambda q: values.append(q.value * 2))

    counter.set_sync(5)

    assert values == [5, 10]


def test_no_callback_on_initial():
    values = []
    counter = quark(42)
    counter.subscribe(lambda q: values.append(q.value))

    assert values == []
    counter.set_sync(43)
    assert values == [43]


def test_no_duplicate_subscription():
    values = []
    counter = quark(0)
    cb = lambda q: values.append(q.value)

    counter.subscribe(cb)
    counter.subscribe(cb)
    counter.set_sync(1)

    assert values == [1]
