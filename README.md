# StateQuark

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

Lightweight atomic state management for Python, designed for IoT devices and embedded systems like Raspberry Pi. StateQuark provides a simple, reactive state management solution perfect for sensor data monitoring, device control, and real-time system state tracking.

## Features

- 🔄 **Reactive State**: Automatic updates when sensor values or device states change
- ⚡ **Derived States**: Computed values that automatically update (e.g., temperature averages, status calculations)
- 🔔 **Subscriptions**: Listen to state changes for alerts, logging, or device control
- 🔀 **Async Support**: Perfect for sensor polling and network communication
- 🧵 **Thread Safe**: Safe for multi-threaded sensor reading and data processing
- 🪶 **Lightweight**: Zero dependencies, minimal memory footprint for embedded systems
- 🎛️ **IoT Ready**: Designed specifically for Raspberry Pi, Arduino, and similar devices

## Installation

```bash
pip install statequark
```

### Development Installation

```bash
git clone https://github.com/minhyeok0328/statequark.git
cd statequark
pip install -e ".[test]"
```

## Quick Start

### Basic Sensor Reading

```python
from statequark import quark

# Temperature sensor state
temperature = quark(20.0)
print(temperature.value)  # 20.0

# Update sensor reading synchronously
temperature.set_sync(25.5)
print(temperature.value)  # 25.5

# Update asynchronously (useful for network sensors)
import asyncio
async def read_network_sensor():
    await temperature.set(23.2)
    print(temperature.value)  # 23.2

asyncio.run(read_network_sensor())
```

### Derived Sensor States

```python
from statequark import quark

# Temperature in Celsius
temp_celsius = quark(25.0)

# Automatically calculate Fahrenheit
def fahrenheit_getter(get):
    celsius = get(temp_celsius)
    return (celsius * 9/5) + 32

temp_fahrenheit = quark(fahrenheit_getter, deps=[temp_celsius])
print(temp_fahrenheit.value)  # 77.0

# When Celsius changes, Fahrenheit updates automatically
temp_celsius.set_sync(30.0)
print(temp_fahrenheit.value)  # 86.0
```

### Multi-Sensor Environment Monitoring

```python
from statequark import quark

# Individual sensor readings
temperature = quark(22.0)
humidity = quark(45.0)
pressure = quark(1013.25)

# Comfort index calculation
def comfort_index_getter(get):
    temp = get(temperature)
    hum = get(humidity)
    # Simple comfort calculation
    if 20 <= temp <= 25 and 40 <= hum <= 60:
        return "Comfortable"
    elif temp > 25 or hum > 60:
        return "Too Hot/Humid"
    else:
        return "Too Cold/Dry"

comfort_index = quark(comfort_index_getter, deps=[temperature, humidity])
print(comfort_index.value)  # "Comfortable"

temperature.set_sync(28.0)
print(comfort_index.value)  # "Too Hot/Humid"
```

### Device State Monitoring with Alerts

```python
from statequark import quark

# Device status
device_online = quark(True)

def on_device_status_change(quark_instance):
    if quark_instance.value:
        print("🟢 Device came online")
        # Could trigger GPIO LED, send notification, etc.
    else:
        print("🔴 Device went offline - Alert!")
        # Could trigger alarm, send email, etc.

# Subscribe to status changes
device_online.subscribe(on_device_status_change)

device_online.set_sync(False)  # Prints: "🔴 Device went offline - Alert!"
device_online.set_sync(True)   # Prints: "🟢 Device came online"

# Unsubscribe when done
device_online.unsubscribe(on_device_status_change)
```

### Complex Example: IoT Greenhouse Monitoring System

```python
from statequark import quark
from typing import Dict, List
import time

# Sensor readings
soil_moisture = quark(65.0)     # Percentage
air_temperature = quark(24.0)   # Celsius
air_humidity = quark(55.0)      # Percentage
light_level = quark(800)        # Lux
water_level = quark(75.0)       # Tank percentage

# System alerts list
alerts = quark([])

# Irrigation system status
def irrigation_needed_getter(get):
    """Auto-determine if irrigation is needed"""
    moisture = get(soil_moisture)
    temp = get(air_temperature)

    # Need water if soil is dry or temperature is high
    return moisture < 40 or (temp > 28 and moisture < 60)

irrigation_needed = quark(irrigation_needed_getter, deps=[soil_moisture, air_temperature])

# Overall system health
def system_health_getter(get):
    """Calculate overall system health score (0-100)"""
    moisture = get(soil_moisture)
    temp = get(air_temperature)
    humidity = get(air_humidity)
    light = get(light_level)
    water = get(water_level)

    # Health scoring logic
    scores = []
    scores.append(100 if 40 <= moisture <= 80 else max(0, 100 - abs(moisture - 60)))
    scores.append(100 if 20 <= temp <= 26 else max(0, 100 - abs(temp - 23) * 5))
    scores.append(100 if 45 <= humidity <= 65 else max(0, 100 - abs(humidity - 55)))
    scores.append(100 if light >= 600 else light / 6)
    scores.append(100 if water >= 20 else water * 5)

    return round(sum(scores) / len(scores))

system_health = quark(system_health_getter, deps=[
    soil_moisture, air_temperature, air_humidity, light_level, water_level
])

# Alert system
def check_alerts(quark_instance):
    """Monitor system and generate alerts"""
    current_alerts = alerts.value.copy()
    timestamp = time.strftime("%H:%M:%S")

    # Check irrigation
    if irrigation_needed.value and water_level.value < 10:
        current_alerts.append(f"{timestamp}: LOW WATER - Cannot irrigate!")
    elif irrigation_needed.value:
        current_alerts.append(f"{timestamp}: Irrigation started")

    # Check system health
    health = system_health.value
    if health < 50:
        current_alerts.append(f"{timestamp}: SYSTEM HEALTH CRITICAL: {health}%")
    elif health < 70:
        current_alerts.append(f"{timestamp}: System health low: {health}%")

    # Keep only last 5 alerts
    if len(current_alerts) > 5:
        current_alerts = current_alerts[-5:]

    alerts.set_sync(current_alerts)

# Subscribe to key changes
irrigation_needed.subscribe(check_alerts)
system_health.subscribe(check_alerts)

# Simulate sensor updates
print(f"Initial System Health: {system_health.value}%")
print(f"Irrigation Needed: {irrigation_needed.value}")

# Simulate dry soil
soil_moisture.set_sync(25.0)
print(f"After soil dried -> Health: {system_health.value}%, Irrigation: {irrigation_needed.value}")
print("Alerts:", alerts.value)

# Simulate hot weather
air_temperature.set_sync(32.0)
print(f"Hot weather -> Health: {system_health.value}%")
print("Alerts:", alerts.value)
```

## API Reference

### `quark(initial_or_getter, deps=None)`

Creates a new Quark instance.

**Parameters:**

- `initial_or_getter`: Initial value or getter function for derived quarks
- `deps`: List of dependent quarks (required for derived quarks)

**Returns:** `Quark[T]` instance

### `Quark` Methods

#### `value: T`

Get the current value of the quark.

#### `set_sync(new_value: T) -> None`

Synchronously set a new value and notify subscribers.

#### `async set(new_value: T) -> None`

Asynchronously set a new value and notify subscribers.

#### `subscribe(callback: Callable) -> None`

Subscribe to value changes.

#### `unsubscribe(callback: Callable) -> None`

Unsubscribe from value changes.

## Testing

Run tests with pytest:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=statequark --cov-report=html
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Run tests (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Use Cases

StateQuark is perfect for:

- **🌡️ Environmental Monitoring**: Temperature, humidity, air quality sensors
- **🏠 Home Automation**: Smart home device state management
- **🌱 Agriculture IoT**: Greenhouse monitoring, irrigation control
- **🏭 Industrial IoT**: Equipment monitoring, predictive maintenance
- **🤖 Robotics**: Sensor fusion, state machines, control systems
- **📊 Data Logging**: Reactive data collection and processing

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
