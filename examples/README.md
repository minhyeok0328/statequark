# StateQuark Examples for IoT Devices

This directory contains practical examples of using StateQuark in IoT and embedded systems.

## Examples

### 1. Basic Sensor (`basic_sensor.py`)
Simple temperature sensor monitoring with real-time updates and alerts.

**Features:**
- Basic quark usage
- Subscriptions for monitoring
- Derived state calculations

**Run:**
```bash
python examples/basic_sensor.py
```

### 2. Persistent Storage (`persistent_storage.py`)
Demonstrates storage utilities for maintaining state across device reboots.

**Features:**
- `quark_with_storage` for persistence
- Session storage (temporary)
- Local storage (persistent)
- Custom storage paths

**Run:**
```bash
python examples/persistent_storage.py
```

### 3. Smart Thermostat (`smart_thermostat.py`)
A complete smart thermostat implementation with climate control logic.

**Features:**
- Multi-sensor integration
- Derived comfort calculations
- Automated control logic
- Storage persistence
- Error handling

**Run:**
```bash
python examples/smart_thermostat.py
```

### 4. Multi-Sensor Dashboard (`multi_sensor_dashboard.py`)
Real-time monitoring dashboard for multiple environmental sensors.

**Features:**
- Multiple sensor quarks
- Real-time data simulation
- Aggregated statistics
- Alert system
- Async sensor polling

**Run:**
```bash
python examples/multi_sensor_dashboard.py
```

### 5. Plant Monitor (`plant_monitor.py`)
Smart plant monitoring system with automated watering logic.

**Features:**
- Soil moisture and temperature monitoring
- Automated watering decisions
- Status tracking
- Storage persistence

**Run:**
```bash
python examples/plant_monitor.py
```

## Requirements

All examples use only StateQuark with no additional dependencies.

## IoT Integration Tips

### Hardware Integration
These examples can be easily adapted for real hardware:

```python
# Replace simulated values with actual sensor readings
import board
import adafruit_dht

# DHT22 sensor on GPIO pin 4
dht_device = adafruit_dht.DHT22(board.D4)

def read_temperature():
    return dht_device.temperature

temperature.set(read_temperature())
```

### Production Deployment
For production use on devices like Raspberry Pi:

1. **Use persistent storage** for critical state
2. **Add error handlers** for sensor failures
3. **Implement graceful shutdown** with cleanup
4. **Use debug mode** during development only
5. **Configure thread pool** based on available resources

```python
from statequark import set_config, StateQuarkConfig

config = StateQuarkConfig(
    debug=False,  # Disable in production
    max_workers=2,  # Limit for Raspberry Pi Zero
    auto_cleanup=True
)
set_config(config)
```

## License

These examples are part of the StateQuark project and are licensed under the MIT License.
