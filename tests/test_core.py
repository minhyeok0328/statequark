import pytest
from statequark import quark

def test_basic_quark():
    count = quark(0)
    assert count.value == 0
    count.set_sync(1)
    assert count.value == 1

def test_derived_quark():
    base = quark(2)
    def double_getter(get):
        return get(base) * 2
    double = quark(double_getter, deps=[base])
    assert double.value == 4
    base.set_sync(3)
    assert double.value == 6