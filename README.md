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
temperature.subscribe(lambda q: print(f"Temp: {q.value}"))
temperature.set_sync(30.0)  # prints: Temp: 30.0

# Reset to initial value
temperature.reset()  # back to 20.0

# Batch updates (single notification)
with batch():
    sensor1.set_sync(25.0)
    sensor2.set_sync(60.0)
```

## Utilities

### Storage (Persistent State)

```python
from statequark import quark_with_storage

# State survives device reboot
config = quark_with_storage("device_config", {"threshold": 25.0})
config.set_sync({"threshold": 30.0})  # Saved to .statequark/device_config.json
```

### Reducer (Action-based Updates)

```python
from statequark import quark_with_reducer

def motor_reducer(state, action):
    match action["type"]:
        case "START": return {**state, "running": True}
        case "SET_SPEED": return {**state, "speed": action["value"]}
    return state

motor = quark_with_reducer({"running": False, "speed": 0}, motor_reducer)
motor.dispatch({"type": "START"})
motor.dispatch({"type": "SET_SPEED", "value": 100})
```

### Select (Partial Subscription)

```python
from statequark import quark, select

sensor = quark({"temp": 25.0, "humidity": 60})
temp = select(sensor, lambda d: d["temp"])  # Only triggers when temp changes
temp.subscribe(lambda q: print(f"Temp changed: {q.value}"))
```

### Family (Dynamic Quarks)

```python
from statequark import quark, quark_family

sensors = quark_family(lambda id: quark(0.0))
living_room = sensors("living_room")
bedroom = sensors("bedroom")
kitchen = sensors("kitchen")
```

### Debounce / Throttle (Noise Filtering)

```python
from statequark import debounce, throttle

# Debounce: wait 100ms of silence before updating
temp = debounce(0.0, 0.1)

# Throttle: max 1 update per second
display = throttle(0, 1.0)
```

### History (Undo/Redo)

```python
from statequark import history

setting = history(50)
setting.set_sync(60)
setting.set_sync(70)
setting.undo()  # 60
setting.undo()  # 50
setting.redo()  # 60
```

### Validate (Value Validation)

```python
from statequark import validate, in_range, clamp

# Raise error on invalid
temp = validate(25.0, in_range(0, 100))

# Auto-clamp on invalid
temp = validate(25.0, in_range(0, 100), clamp(0, 100))
temp.set_sync(150)  # Clamped to 100
```

### Middleware (Extensible Hooks)

```python
from statequark import middleware, logger, persist

storage = {}
counter = middleware(0)
counter.use(logger("counter"))  # Log changes
counter.use(persist(storage, "count"))  # Save to dict
counter.set_sync(42)  # [counter] 0 -> 42
```

### Loadable (Async State)

```python
from statequark import quark, loadable

data = quark(None)
state = loadable(data)
state.set_loading()   # state.value.state == "loading"
state.set_data(42)    # state.value.state == "hasData"
state.set_error(err)  # state.value.state == "hasError"
```

## IoT Example

```python
from statequark import quark, quark_with_storage, validate, in_range, clamp

# Persistent config
config = quark_with_storage("config", {"threshold": 30})

# Validated sensor with auto-clamp
soil = validate(65.0, in_range(0, 100), clamp(0, 100))

# Derived alert
alert = quark(
    lambda get: get(soil) < get(config)["threshold"],
    deps=[soil, config]
)

# Hardware control
alert.subscribe(lambda q: gpio.output(PUMP_PIN, q.value))
```

## API Reference

### Core

| Function | Description |
|----------|-------------|
| `quark(value)` | Create state |
| `quark(fn, deps=[...])` | Create derived state |
| `batch()` | Batch updates context |

### Quark Methods

| Method | Description |
|--------|-------------|
| `.value` | Get current value |
| `.set_sync(v)` | Set value (sync) |
| `await .set(v)` | Set value (async) |
| `.reset()` | Reset to initial |
| `.subscribe(fn)` | Subscribe to changes |
| `.unsubscribe(fn)` | Unsubscribe |
| `.cleanup()` | Release resources |

### Utilities

| Function | Description |
|----------|-------------|
| `quark_with_storage(key, default)` | Persistent state |
| `quark_with_reducer(init, reducer)` | Action-based state |
| `select(source, selector)` | Partial subscription |
| `quark_family(factory)` | Dynamic quark creation |
| `debounce(init, delay)` | Debounced updates |
| `throttle(init, interval)` | Throttled updates |
| `history(init, max_size)` | Undo/redo support |
| `validate(init, validator, on_invalid)` | Value validation |
| `middleware(init)` | Middleware pipeline |
| `loadable(source)` | Async state wrapper |

## License

MIT
