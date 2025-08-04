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
- 🛡️ **Error Handling**: Custom error handlers for robust IoT applications
- 🧹 **Resource Management**: Built-in cleanup for long-running applications
- 🪶 **Lightweight**: Shared thread pool, minimal memory footprint for embedded systems
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

### Basic Usage

```python
from statequark import quark

# Create a reactive state
temperature = quark(20.0)
print(temperature.value)  # 20.0

# Update values
temperature.set_sync(25.5)  # Synchronous
print(temperature.value)  # 25.5

# Or update asynchronously
import asyncio
await temperature.set(23.2)  # Async update
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
temp_celsius.set_sync(30.0)
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

temperature.set_sync(28.0)
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

device_online.set_sync(False)  # Prints: "Device: 🔴 Offline"
device_online.set_sync(True)   # Prints: "Device: 🟢 Online"
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
soil_moisture.set_sync(20.0)
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
temperature_sensor.set_sync(150)  # Error logged and handled gracefully
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

## API Reference

### `quark(initial_or_getter, deps=None, error_handler=None)`

Creates a new Quark instance.

**Parameters:**

- `initial_or_getter`: Initial value or getter function for derived quarks
- `deps`: List of dependent quarks (required for derived quarks)
- `error_handler`: Optional custom error handler function

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

#### `cleanup() -> None`

Clean up resources to prevent memory leaks in long-running applications. Removes all dependencies and callbacks.

#### `set_error_handler(handler: Optional[ErrorHandler]) -> None`

Set or update the custom error handler for callback exceptions.

**Parameters:**

- `handler`: Error handler function or `None` to use default handling

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
