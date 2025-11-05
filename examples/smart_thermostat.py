#!/usr/bin/env python3
"""
Smart Thermostat Example

A complete smart thermostat implementation demonstrating multi-sensor
integration, derived state calculations, and persistent storage.
"""

import time
from statequark import quark, quark_with_storage, StorageType


class SmartThermostat:
    """Smart thermostat with climate control logic."""

    def __init__(self):
        """Initialize the smart thermostat."""
        # Load persistent settings
        self.target_temp = quark_with_storage(
            "thermostat_target", 22.0, StorageType.LOCAL
        )

        self.mode = quark_with_storage(
            "thermostat_mode", "auto", StorageType.LOCAL
        )

        # Current sensor readings (volatile)
        self.current_temp = quark(20.0)
        self.current_humidity = quark(50.0)

        # Derived states
        self.heating_needed = quark(
            lambda get: get(self.current_temp) < get(self.target_temp) - 1.0,
            deps=[self.current_temp, self.target_temp],
        )

        self.cooling_needed = quark(
            lambda get: get(self.current_temp) > get(self.target_temp) + 1.0,
            deps=[self.current_temp, self.target_temp],
        )

        # Comfort index (0-100, higher is more comfortable)
        def calculate_comfort(get):
            temp = get(self.current_temp)
            humidity = get(self.current_humidity)
            target = get(self.target_temp)

            # Temperature difference penalty
            temp_diff = abs(temp - target)
            temp_score = max(0, 100 - (temp_diff * 10))

            # Humidity optimal range: 40-60%
            humidity_diff = 0
            if humidity < 40:
                humidity_diff = 40 - humidity
            elif humidity > 60:
                humidity_diff = humidity - 60
            humidity_score = max(0, 100 - (humidity_diff * 2))

            return (temp_score + humidity_score) / 2

        self.comfort_index = quark(
            calculate_comfort,
            deps=[self.current_temp, self.current_humidity, self.target_temp],
        )

        # Setup subscriptions
        self._setup_subscriptions()

    def _setup_subscriptions(self):
        """Setup monitoring subscriptions."""

        def on_heating_change(q):
            if q.value:
                print("🔥 Heating: ON")
            else:
                print("⚪ Heating: OFF")

        def on_cooling_change(q):
            if q.value:
                print("❄️  Cooling: ON")
            else:
                print("⚪ Cooling: OFF")

        def on_comfort_change(q):
            comfort = q.value
            if comfort >= 80:
                emoji = "😊"
                status = "Excellent"
            elif comfort >= 60:
                emoji = "🙂"
                status = "Good"
            elif comfort >= 40:
                emoji = "😐"
                status = "Fair"
            else:
                emoji = "😰"
                status = "Poor"

            print(f"{emoji} Comfort Index: {comfort:.1f}/100 ({status})")

        self.heating_needed.subscribe(on_heating_change)
        self.cooling_needed.subscribe(on_cooling_change)
        self.comfort_index.subscribe(on_comfort_change)

    def update_sensors(self, temperature: float, humidity: float):
        """Update sensor readings."""
        self.current_temp.set(temperature)
        self.current_humidity.set(humidity)

    def set_target_temperature(self, temp: float):
        """Set target temperature (persists across reboots)."""
        print(f"🎯 Target temperature set to: {temp}°C")
        self.target_temp.set(temp)

    def get_status(self):
        """Get current thermostat status."""
        return {
            "current_temp": self.current_temp.value,
            "current_humidity": self.current_humidity.value,
            "target_temp": self.target_temp.value,
            "mode": self.mode.value,
            "heating": self.heating_needed.value,
            "cooling": self.cooling_needed.value,
            "comfort": self.comfort_index.value,
        }


def main():
    print("=== Smart Thermostat Example ===\n")

    # Initialize thermostat
    thermostat = SmartThermostat()

    print("Initial Status:")
    status = thermostat.get_status()
    print(f"  Temperature: {status['current_temp']}°C")
    print(f"  Humidity: {status['current_humidity']}%")
    print(f"  Target: {status['target_temp']}°C")
    print(f"  Mode: {status['mode']}\n")

    # Set target temperature
    thermostat.set_target_temperature(23.0)
    print()

    # Simulate sensor readings throughout the day
    print("Simulating daily temperature changes:\n")

    scenarios = [
        (18.0, 55.0, "Morning - Cold"),
        (20.0, 52.0, "Warming up"),
        (22.0, 50.0, "Approaching target"),
        (23.0, 48.0, "At target"),
        (25.0, 45.0, "Afternoon - Getting warm"),
        (27.0, 42.0, "Too warm"),
        (24.0, 46.0, "Cooling down"),
        (22.0, 50.0, "Evening - Comfortable"),
    ]

    for temp, humidity, description in scenarios:
        print(f"--- {description} ---")
        print(f"📊 Sensors: {temp}°C, {humidity}%")
        thermostat.update_sensors(temp, humidity)
        print()
        time.sleep(0.5)

    print("=== Example Complete ===")
    print("\n💡 The target temperature and mode are stored in ./.statequark/")
    print("   They will persist if you run this example again!")


if __name__ == "__main__":
    main()
