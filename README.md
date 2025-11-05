# StateQuark

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Typed with mypy](https://img.shields.io/badge/typed-mypy-blue.svg)](http://mypy-lang.org/)

Lightweight atomic state management for Python, designed for IoT devices and embedded systems like Raspberry Pi. StateQuark provides a simple, reactive state management solution perfect for sensor data monitoring, device control, and real-time system state tracking.

Inspired by [Jotai](https://jotai.org/), StateQuark brings atomic state management to the embedded world with a focus on resource efficiency, thread safety, and ease of use.

## Features

- 🔄 **Reactive State**: Automatic updates when sensor values or device states change
- ⚡ **Derived States**: Computed values that automatically update (e.g., temperature averages, status calculations)
- 🔔 **Subscriptions**: Listen to state changes for alerts, logging, or device control
- 🔀 **Async Support**: Perfect for sensor polling and network communication
- 🧵 **Thread Safe**: Safe for multi-threaded sensor reading and data processing
- 🛡️ **Error Handling**: Custom error handlers for robust IoT applications
- 🧹 **Resource Management**: Built-in cleanup for long-running applications with context managers
- 🪶 **Lightweight**: Shared thread pool, minimal memory footprint for embedded systems
- 🎛️ **IoT Ready**: Designed specifically for Raspberry Pi, Arduino, and similar devices
- 🐛 **Debug Mode**: Comprehensive logging for development and troubleshooting
- ⚙️ **Configurable**: Flexible configuration system for resource constraints
- 📝 **Type Safe**: Full type hints with mypy support for Python 3.10+

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

### Basic Usage

```python
from statequark import quark

# Create a reactive state
temperature = quark(20.0)
print(temperature.value)  # 20.0

# Update values (synchronous by default)
temperature.set(25.5)
print(temperature.value)  # 25.5

# Or update asynchronously when needed
import asyncio
await temperature.set_async(23.2)  # Async update
```

### Derived States

```python
# Temperature in Celsius
temp_celsius = quark(25.0)

# Auto-calculated Fahrenheit
def to_fahrenheit(get):
    return get(temp_celsius) * 9/5 + 32

temp_fahrenheit = quark(to_fahrenheit, deps=[temp_celsius])
print(temp_fahrenheit.value)  # 77.0

# Updates automatically when dependency changes
temp_celsius.set(30.0)
print(temp_fahrenheit.value)  # 86.0
```

### Multi-Sensor Example

```python
# Sensor readings
temperature = quark(22.0)
humidity = quark(45.0)

# Derived comfort status
def comfort_status(get):
    temp, hum = get(temperature), get(humidity)
    if 20 <= temp <= 25 and 40 <= hum <= 60:
        return "Comfortable"
    return "Uncomfortable"

comfort = quark(comfort_status, deps=[temperature, humidity])
print(comfort.value)  # "Comfortable"

temperature.set(28.0)
print(comfort.value)  # "Uncomfortable"
```

### Subscriptions and Alerts

```python
# Device status monitoring
device_online = quark(True)

def on_status_change(q):
    status = "🟢 Online" if q.value else "🔴 Offline"
    print(f"Device: {status}")

# Subscribe to changes
device_online.subscribe(on_status_change)

device_online.set(False)  # Prints: "Device: 🔴 Offline"
device_online.set(True)   # Prints: "Device: 🟢 Online"
```

### IoT Example: Smart Plant Monitor

```python
# Sensor data
soil_moisture = quark(65.0)
temperature = quark(24.0)

# Derived states
def needs_water(get):
    moisture = get(soil_moisture)
    temp = get(temperature)
    return moisture < 30 or (temp > 28 and moisture < 50)

def plant_status(get):
    if get(needs_water):
        return "🚰 Needs watering"
    return "🌱 Healthy"

water_alert = quark(needs_water, deps=[soil_moisture, temperature])
status = quark(plant_status, deps=[water_alert])

print(status.value)  # "🌱 Healthy"

# Simulate dry conditions
soil_moisture.set(20.0)
print(status.value)  # "🚰 Needs watering"
```

### Error Handling

```python
# Custom error handler for IoT applications
def iot_error_handler(error, callback, quark_instance):
    timestamp = datetime.now().isoformat()
    error_msg = f"[{timestamp}] Sensor error: {error}"

    # Log to file
    with open("/var/log/sensors.log", "a") as f:
        f.write(error_msg + "\n")

    # Send alert for critical errors
    if "critical" in str(error).lower():
        send_sms_alert(error_msg)

# Create sensor with error handler
temperature_sensor = quark(22.0, error_handler=iot_error_handler)

# Or set error handler later
humidity_sensor = quark(60.0)
humidity_sensor.set_error_handler(iot_error_handler)

def faulty_callback(q):
    if q.value > 100:
        raise ValueError("Sensor reading out of range!")

temperature_sensor.subscribe(faulty_callback)
temperature_sensor.set(150)  # Error logged and handled gracefully
```

### Resource Management

```python
# Long-running IoT application
temperature = quark(20.0)
humidity = quark(50.0)

# Create derived state
def comfort_index(get):
    temp = get(temperature)
    hum = get(humidity)
    return (temp * 0.6) + (hum * 0.4)

comfort = quark(comfort_index, deps=[temperature, humidity])

# Add monitoring callbacks
def log_comfort_change(q):
    print(f"Comfort index: {q.value}")

comfort.subscribe(log_comfort_change)

# When shutting down or replacing sensors
def shutdown_system():
    comfort.cleanup()  # Removes dependencies and callbacks
    print("System safely shut down")

# Use with signal handlers for graceful shutdown
import signal
signal.signal(signal.SIGTERM, lambda s, f: shutdown_system())
```

### Debug Mode

```python
from statequark import quark, enable_debug, disable_debug

# Enable debug logging for development
enable_debug()

# All operations will be logged
temperature = quark(20.0)
temperature.set(25.5)
# Logs: "Created Quark #1 with initial value: 20.0"
# Logs: "Quark #1 value changed: 20.0 -> 25.5"

# Disable when not needed
disable_debug()
```

### Configuration

```python
from statequark import StateQuarkConfig, set_config

# Configure for resource-constrained devices
config = StateQuarkConfig(
    debug=True,              # Enable debug logging
    max_workers=2,           # Limit thread pool size
    thread_name_prefix="sensor",
    auto_cleanup=True        # Auto cleanup on exit
)

set_config(config)
```

### Context Manager

```python
from statequark import quark

# Automatic cleanup with context manager
with quark(20.0) as temperature:
    def on_change(q):
        print(f"Temperature: {q.value}°C")

    temperature.subscribe(on_change)
    temperature.set(25.0)
    # Output: "Temperature: 25.0°C"

# Resources automatically cleaned up after context exit
```

### Production Example

```python
from statequark import quark
import logging

# Production error handler with logging
def production_error_handler(error, callback, sensor):
    logging.error(f"Sensor {callback.__name__} error: {error}")
    if sensor.value > 35:  # Critical temperature
        os.system("echo 'Temperature alert!' | mail admin@example.com")

# Initialize sensors
soil_temp = quark(22.0, error_handler=production_error_handler)
soil_moisture = quark(65.0, error_handler=production_error_handler)

# Automation logic
irrigation_needed = quark(
    lambda get: get(soil_moisture) < 30 or get(soil_temp) > 28,
    deps=[soil_moisture, soil_temp]
)

# Hardware control with error handling
def control_pump(q):
    gpio.output(PUMP_PIN, gpio.HIGH if q.value else gpio.LOW)
    logging.info(f"Pump {'ON' if q.value else 'OFF'}")

irrigation_needed.subscribe(control_pump)

# Graceful shutdown
def shutdown():
    irrigation_needed.cleanup()
    gpio.cleanup()

signal.signal(signal.SIGTERM, lambda s, f: shutdown())
```

### Storage Utilities

StateQuark includes storage utilities for persisting state across device reboots:

```python
from statequark import quark_with_storage, StorageType

# Session storage (temporary, stored in /tmp/statequark/)
temp_sensor = quark_with_storage(
    "temperature",
    20.0,
    StorageType.SESSION
)

# Local storage (persistent, stored in ./.statequark/)
humidity_sensor = quark_with_storage(
    "humidity",
    50.0,
    StorageType.LOCAL
)

# Custom storage path
pressure_sensor = quark_with_storage(
    "pressure",
    1013.25,
    StorageType.LOCAL,
    base_path="/var/lib/myapp"
)

# Values automatically persist across program restarts
temp_sensor.set(25.5)
```

### Additional Utilities

```python
from statequark import quark_with_reset, quark_with_default

# Quark with reset capability (factory reset)
sensor_value, reset_sensor = quark_with_reset(20.0)
sensor_value.set(25.5)
reset_sensor.set(None)  # Resets sensor_value to 20.0

# Quark with fallback value for error handling
sensor = quark(None)
def get_value(get):
    val = get(sensor)
    if val is None:
        raise ValueError("Sensor disconnected")
    return val

safe_sensor = quark_with_default(get_value, [sensor], 0.0)
```

## Examples

Check out the `examples/` directory for complete IoT application examples:

- **basic_sensor.py** - Simple temperature sensor monitoring
- **persistent_storage.py** - Storage utilities demonstration
- **smart_thermostat.py** - Complete thermostat with climate control
- **multi_sensor_dashboard.py** - Real-time multi-sensor monitoring
- **plant_monitor.py** - Smart plant care system

Run any example:
```bash
python examples/basic_sensor.py
```

See [examples/README.md](examples/README.md) for detailed documentation.

## API Reference

### Core API

#### `quark(initial_or_getter, deps=None, error_handler=None)`

Creates a new Quark instance.

**Parameters:**

- `initial_or_getter`: Initial value or getter function for derived quarks
- `deps`: List of dependent quarks (required for derived quarks)
- `error_handler`: Optional custom error handler function

**Returns:** `Quark[T]` instance

**Example:**
```python
# Simple quark
counter = quark(0)

# Derived quark
doubled = quark(lambda get: get(counter) * 2, deps=[counter])
```

### Quark Methods

#### `value: T`

Get the current value of the quark.

#### `set(new_value: T) -> None`

Synchronously set a new value and notify subscribers. This is the default method for updating values.

#### `async set_async(new_value: T) -> None`

Asynchronously set a new value and notify subscribers. Use when async execution is needed.

#### `subscribe(callback: Callable) -> None`

Subscribe to value changes.

#### `unsubscribe(callback: Callable) -> None`

Unsubscribe from value changes.

#### `cleanup() -> None`

Clean up resources to prevent memory leaks. Removes all dependencies and callbacks.

#### `set_error_handler(handler: Optional[ErrorHandler]) -> None`

Set or update the custom error handler for callback exceptions.

### Configuration API

#### `StateQuarkConfig`

Configuration dataclass for StateQuark.

**Parameters:**
- `debug: bool = False` - Enable debug logging
- `max_workers: int = 4` - Thread pool size (1-32)
- `thread_name_prefix: str = "quark-callback"` - Thread naming prefix
- `auto_cleanup: bool = True` - Auto cleanup on exit

#### `enable_debug() -> None`

Enable debug logging for detailed operation tracking.

#### `disable_debug() -> None`

Disable debug logging.

#### `get_config() -> StateQuarkConfig`

Get the current global configuration.

#### `set_config(config: StateQuarkConfig) -> None`

Set a new global configuration.

#### `reset_config() -> None`

Reset configuration to default values.

### Utility Functions

#### `cleanup_executor() -> None`

Manually cleanup the shared thread pool executor. Usually handled automatically.

#### `quark_with_storage(key: str, initial_value: T, storage_type: StorageType, base_path: Optional[str] = None) -> Quark[T]`

Create a quark with persistent storage. Values are automatically saved to disk and restored on program restart.

**Parameters:**
- `key`: Unique storage key
- `initial_value`: Default value if no stored value exists
- `storage_type`: `StorageType.SESSION` (temporary) or `StorageType.LOCAL` (persistent)
- `base_path`: Custom base directory for LOCAL storage (optional)

#### `quark_with_reset(initial_value: T) -> tuple[Quark[T], Quark[None]]`

Create a quark with reset capability. Returns a tuple of (value_quark, reset_quark).

#### `quark_with_default(get_default: callable, deps: list[Quark[Any]], fallback: T) -> Quark[T]`

Create a derived quark with a fallback value. If the getter function raises an exception, the fallback value is used

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

- **🌡️ Environmental Monitoring**: Temperature, humidity, air quality sensors with error logging
- **🏠 Home Automation**: Smart home device state management with graceful failure handling
- **🌱 Agriculture IoT**: Greenhouse monitoring, irrigation control with production-ready error handling
- **🏭 Industrial IoT**: Equipment monitoring, predictive maintenance with robust error recovery
- **🤖 Robotics**: Sensor fusion, state machines, control systems with resource cleanup
- **📊 Data Logging**: Reactive data collection and processing with memory leak prevention
- **🚨 Critical Systems**: Mission-critical applications requiring 24/7 uptime on Raspberry Pi

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
