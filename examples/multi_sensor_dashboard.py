#!/usr/bin/env python3
"""
Multi-Sensor Dashboard Example

Real-time monitoring dashboard for multiple environmental sensors.
Demonstrates async sensor polling and aggregated statistics.
"""

import asyncio
import random
import time
from statequark import quark, enable_debug


class SensorDashboard:
    """Multi-sensor monitoring dashboard."""

    def __init__(self):
        """Initialize the sensor dashboard."""
        # Individual sensors
        self.temperature = quark(20.0)
        self.humidity = quark(50.0)
        self.pressure = quark(1013.25)
        self.air_quality = quark(100)  # AQI: 0-500

        # Derived statistics
        self.avg_temp_readings = []
        self.max_readings = 10

        def calculate_avg_temp(get):
            """Calculate rolling average temperature."""
            temp = get(self.temperature)
            self.avg_temp_readings.append(temp)
            if len(self.avg_temp_readings) > self.max_readings:
                self.avg_temp_readings.pop(0)
            return sum(self.avg_temp_readings) / len(self.avg_temp_readings)

        self.avg_temperature = quark(calculate_avg_temp, deps=[self.temperature])

        # Environmental status
        def get_air_quality_status(get):
            aqi = get(self.air_quality)
            if aqi <= 50:
                return "Good"
            elif aqi <= 100:
                return "Moderate"
            elif aqi <= 150:
                return "Unhealthy for Sensitive Groups"
            elif aqi <= 200:
                return "Unhealthy"
            elif aqi <= 300:
                return "Very Unhealthy"
            else:
                return "Hazardous"

        self.air_quality_status = quark(
            get_air_quality_status, deps=[self.air_quality]
        )

        # Weather description
        def get_weather_description(get):
            temp = get(self.temperature)
            humidity = get(self.humidity)
            pressure = get(self.pressure)

            conditions = []

            if temp < 10:
                conditions.append("Cold")
            elif temp > 25:
                conditions.append("Hot")
            else:
                conditions.append("Mild")

            if humidity > 70:
                conditions.append("Humid")
            elif humidity < 30:
                conditions.append("Dry")

            if pressure < 1000:
                conditions.append("Low Pressure")
            elif pressure > 1020:
                conditions.append("High Pressure")

            return ", ".join(conditions) if conditions else "Normal"

        self.weather_description = quark(
            get_weather_description,
            deps=[self.temperature, self.humidity, self.pressure],
        )

        # Alert system
        self._setup_alerts()

    def _setup_alerts(self):
        """Setup alert subscriptions."""

        def temp_alert(q):
            if q.value > 35:
                print(f"  🚨 CRITICAL: Temperature too high: {q.value}°C")
            elif q.value < 0:
                print(f"  🚨 CRITICAL: Temperature too low: {q.value}°C")

        def humidity_alert(q):
            if q.value > 80:
                print(f"  ⚠️  WARNING: High humidity: {q.value}%")
            elif q.value < 20:
                print(f"  ⚠️  WARNING: Low humidity: {q.value}%")

        def air_quality_alert(q):
            status = self.air_quality_status.value
            if status in ["Unhealthy", "Very Unhealthy", "Hazardous"]:
                print(f"  🚨 AIR QUALITY ALERT: {status} (AQI: {q.value})")

        self.temperature.subscribe(temp_alert)
        self.humidity.subscribe(humidity_alert)
        self.air_quality.subscribe(air_quality_alert)

    def update_sensors(self, temp, humidity, pressure, aqi):
        """Update all sensor readings."""
        self.temperature.set(temp)
        self.humidity.set(humidity)
        self.pressure.set(pressure)
        self.air_quality.set(aqi)

    def display_dashboard(self):
        """Display current dashboard status."""
        print("\n" + "=" * 60)
        print("📊 ENVIRONMENTAL MONITORING DASHBOARD")
        print("=" * 60)
        print(f"🌡️  Temperature:     {self.temperature.value:.1f}°C")
        print(f"    Avg (last {len(self.avg_temp_readings)}):  {self.avg_temperature.value:.1f}°C")
        print(f"💧 Humidity:        {self.humidity.value:.1f}%")
        print(f"🌀 Pressure:        {self.pressure.value:.2f} hPa")
        print(f"🌫️  Air Quality:     {self.air_quality.value} AQI ({self.air_quality_status.value})")
        print(f"☁️  Conditions:      {self.weather_description.value}")
        print("=" * 60)


async def simulate_sensors(dashboard):
    """Simulate async sensor readings."""
    base_temp = 22.0
    base_humidity = 50.0
    base_pressure = 1013.25
    base_aqi = 50

    for i in range(15):
        # Simulate sensor drift and noise
        temp = base_temp + random.uniform(-2, 5) + (i * 0.3)
        humidity = base_humidity + random.uniform(-10, 10)
        pressure = base_pressure + random.uniform(-5, 5)
        aqi = max(0, base_aqi + random.uniform(-20, 30))

        dashboard.update_sensors(temp, humidity, pressure, aqi)
        dashboard.display_dashboard()

        await asyncio.sleep(1.5)


def main():
    print("=== Multi-Sensor Dashboard Example ===")
    print("Monitoring environmental conditions in real-time\n")
    print("Press Ctrl+C to stop\n")

    # Create dashboard
    dashboard = SensorDashboard()

    # Run async simulation
    try:
        asyncio.run(simulate_sensors(dashboard))
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
