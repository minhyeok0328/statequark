# StateQuark

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Atomic state management for IoT and embedded systems. Inspired by [Jotai](https://jotai.org/).

## Installation

```bash
pip install statequark
```

## Quick Start

```python
from statequark import quark, batch

# Basic state
temperature = quark(20.0)
print(temperature.value)  # 20.0
temperature.set_sync(25.5)

# Derived state (auto-updates when dependencies change)
temp_f = quark(lambda get: get(temperature) * 9/5 + 32, deps=[temperature])
print(temp_f.value)  # 77.9

# Subscriptions
def on_change(q):
    print(f"Temperature: {q.value}")

temperature.subscribe(on_change)
temperature.set_sync(30.0)  # prints: Temperature: 30.0

# Reset to initial value
temperature.reset()  # back to 20.0

# Batch updates (single notification)
with batch():
    sensor1.set_sync(25.0)
    sensor2.set_sync(60.0)
```

## IoT Example

```python
from statequark import quark

# Sensors
soil_moisture = quark(65.0)
temperature = quark(24.0)

# Derived status
def needs_water(get):
    return get(soil_moisture) < 30 or get(temperature) > 28

water_alert = quark(needs_water, deps=[soil_moisture, temperature])

# Hardware control
def control_pump(q):
    gpio.output(PUMP_PIN, gpio.HIGH if q.value else gpio.LOW)

water_alert.subscribe(control_pump)

# Cleanup on shutdown
water_alert.cleanup()
```

## Configuration

```python
from statequark import StateQuarkConfig, set_config, enable_debug

# Resource-constrained devices
set_config(StateQuarkConfig(
    max_workers=2,      # Thread pool size (1-32)
    auto_cleanup=True   # Cleanup on exit
))

# Debug mode
enable_debug()
```

## API

| Method | Description |
|--------|-------------|
| `quark(value)` | Create state |
| `quark(fn, deps=[...])` | Create derived state |
| `.value` | Get current value |
| `.set_sync(v)` | Set value (sync) |
| `await .set(v)` | Set value (async) |
| `.reset()` | Reset to initial value |
| `.subscribe(fn)` | Subscribe to changes |
| `.unsubscribe(fn)` | Unsubscribe |
| `.cleanup()` | Release resources |
| `batch()` | Batch updates context |

## License

MIT
