"""Derived quark functionality tests."""
import pytest
from statequark import quark


def test_simple_derived_quark():
    """Test basic derived quark functionality."""
    base = quark(2)
    
    def double_getter(get):
        return get(base) * 2
    
    double = quark(double_getter, deps=[base])
    assert double.value == 4
    
    base.set_sync(3)
    assert double.value == 6


def test_derived_with_multiple_dependencies():
    """Test derived quark with multiple dependencies."""
    temp = quark(25.0)
    humidity = quark(60.0)
    
    def comfort_index(get):
        t = get(temp)
        h = get(humidity)
        return "comfortable" if 20 <= t <= 26 and 40 <= h <= 70 else "uncomfortable"
    
    comfort = quark(comfort_index, deps=[temp, humidity])
    assert comfort.value == "comfortable"
    
    # Change temperature
    temp.set_sync(30.0)
    assert comfort.value == "uncomfortable"
    
    # Reset temperature, change humidity
    temp.set_sync(22.0)
    humidity.set_sync(80.0)
    assert comfort.value == "uncomfortable"
    
    # Both back to normal
    humidity.set_sync(50.0)
    assert comfort.value == "comfortable"


def test_nested_derived_quarks():
    """Test derived quarks depending on other derived quarks."""
    base = quark(2)
    
    def double(get):
        return get(base) * 2
    
    def quadruple(get):
        return get(doubled) * 2
    
    doubled = quark(double, deps=[base])
    quadrupled = quark(quadruple, deps=[doubled])
    
    assert doubled.value == 4
    assert quadrupled.value == 8
    
    base.set_sync(3)
    assert doubled.value == 6
    assert quadrupled.value == 12


def test_complex_derived_calculation():
    """Test more complex derived calculations."""
    # Temperature sensors in different rooms
    living_room = quark(22.0)
    bedroom = quark(20.0)
    kitchen = quark(24.0)
    
    def average_temp(get):
        temps = [get(living_room), get(bedroom), get(kitchen)]
        return sum(temps) / len(temps)
    
    def temp_variance(get):
        temps = [get(living_room), get(bedroom), get(kitchen)]
        avg = get(avg_temp)
        return sum((t - avg) ** 2 for t in temps) / len(temps)
    
    avg_temp = quark(average_temp, deps=[living_room, bedroom, kitchen])
    variance = quark(temp_variance, deps=[living_room, bedroom, kitchen, avg_temp])
    
    assert avg_temp.value == 22.0
    assert variance.value == pytest.approx(2.67, rel=1e-2)
    
    # Change one temperature
    bedroom.set_sync(18.0)
    expected_avg = (22.0 + 18.0 + 24.0) / 3
    assert avg_temp.value == pytest.approx(expected_avg, rel=1e-2)


def test_derived_quark_cannot_be_set():
    """Test that derived quarks cannot be set directly."""
    base = quark(5)
    
    def derived_getter(get):
        return get(base) * 2
    
    derived = quark(derived_getter, deps=[base])
    
    with pytest.raises(ValueError, match="Cannot set derived quark directly"):
        derived.set_sync(10)


def test_derived_quark_with_conditional_logic():
    """Test derived quarks with conditional logic."""
    sensor_value = quark(50.0)
    threshold = quark(75.0)
    
    def alarm_status(get):
        value = get(sensor_value)
        limit = get(threshold)
        
        if value > limit:
            return "ALARM"
        elif value > limit * 0.8:
            return "WARNING"
        else:
            return "NORMAL"
    
    status = quark(alarm_status, deps=[sensor_value, threshold])
    assert status.value == "NORMAL"
    
    # Trigger warning
    sensor_value.set_sync(65.0)  # 65 > 75 * 0.8 (60)
    assert status.value == "WARNING"
    
    # Trigger alarm
    sensor_value.set_sync(80.0)
    assert status.value == "ALARM"
    
    # Change threshold
    threshold.set_sync(90.0)
    assert status.value == "WARNING"  # 80 > 90 * 0.8 (72)


def test_derived_quark_with_string_operations():
    """Test derived quarks with string manipulations."""
    first_name = quark("John")
    last_name = quark("Doe")
    
    def full_name(get):
        return f"{get(first_name)} {get(last_name)}"
    
    def initials(get):
        fname = get(first_name)
        lname = get(last_name)
        return f"{fname[0]}.{lname[0]}."
    
    name = quark(full_name, deps=[first_name, last_name])
    init = quark(initials, deps=[first_name, last_name])
    
    assert name.value == "John Doe"
    assert init.value == "J.D."
    
    first_name.set_sync("Jane")
    assert name.value == "Jane Doe"
    assert init.value == "J.D."
    
    last_name.set_sync("Smith")
    assert name.value == "Jane Smith"
    assert init.value == "J.S."