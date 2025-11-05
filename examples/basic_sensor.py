#!/usr/bin/env python3
"""
Basic Sensor Example

Demonstrates basic StateQuark usage for a simple temperature sensor.
Perfect for getting started with IoT device monitoring.
"""

import time
from statequark import quark


def main():
    print("=== Basic Sensor Example ===\n")

    # Create a temperature sensor quark
    temperature = quark(20.0)
    print(f"Initial temperature: {temperature.value}°C")

    # Create a derived state for Fahrenheit
    def celsius_to_fahrenheit(get):
        celsius = get(temperature)
        return celsius * 9 / 5 + 32

    temp_fahrenheit = quark(celsius_to_fahrenheit, deps=[temperature])
    print(f"Temperature in Fahrenheit: {temp_fahrenheit.value}°F\n")

    # Subscribe to temperature changes
    def on_temperature_change(q):
        print(f"  📊 Temperature updated: {q.value}°C ({temp_fahrenheit.value}°F)")

    def temperature_alert(q):
        if q.value > 30:
            print(f"  ⚠️  HIGH TEMPERATURE ALERT: {q.value}°C")
        elif q.value < 10:
            print(f"  ❄️  LOW TEMPERATURE ALERT: {q.value}°C")

    temperature.subscribe(on_temperature_change)
    temperature.subscribe(temperature_alert)

    # Simulate sensor readings
    print("Simulating sensor readings:\n")
    readings = [22.5, 25.0, 28.5, 32.0, 35.5, 30.0, 25.0, 18.0, 8.0, 15.0]

    for reading in readings:
        temperature.set(reading)
        time.sleep(0.5)

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
