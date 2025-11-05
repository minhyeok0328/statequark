#!/usr/bin/env python3
"""
Plant Monitor Example

Smart plant monitoring system with automated watering logic.
Demonstrates IoT application for automated gardening.
"""

import time
from statequark import quark, quark_with_storage, StorageType


class PlantMonitor:
    """Smart plant monitoring and watering system."""

    def __init__(self, plant_name: str):
        """Initialize plant monitor."""
        self.plant_name = plant_name

        # Sensor readings (volatile)
        self.soil_moisture = quark(65.0)  # 0-100%
        self.temperature = quark(24.0)  # Celsius
        self.light_level = quark(500.0)  # Lux

        # Persistent settings
        self.moisture_threshold = quark_with_storage(
            f"{plant_name}_moisture_threshold", 30.0, StorageType.LOCAL
        )

        self.watering_duration = quark_with_storage(
            f"{plant_name}_watering_duration", 5.0, StorageType.LOCAL
        )

        # Watering history (persistent)
        self.last_watered = quark_with_storage(
            f"{plant_name}_last_watered", "Never", StorageType.LOCAL
        )

        self.total_waterings = quark_with_storage(
            f"{plant_name}_total_waterings", 0, StorageType.LOCAL
        )

        # Derived states
        def needs_water(get):
            """Determine if plant needs water."""
            moisture = get(self.soil_moisture)
            threshold = get(self.moisture_threshold)
            temp = get(self.temperature)

            # Need water if:
            # 1. Moisture below threshold, OR
            # 2. High temperature and moisture below 50%
            return moisture < threshold or (temp > 28 and moisture < 50)

        self.needs_watering = quark(
            needs_water,
            deps=[self.soil_moisture, self.moisture_threshold, self.temperature],
        )

        def plant_health(get):
            """Calculate plant health status."""
            moisture = get(self.soil_moisture)
            temp = get(self.temperature)
            light = get(self.light_level)

            # Health factors
            moisture_ok = 30 <= moisture <= 70
            temp_ok = 18 <= temp <= 28
            light_ok = light >= 200  # Minimum light for growth

            score = sum([moisture_ok, temp_ok, light_ok])

            if score == 3:
                return "Excellent"
            elif score == 2:
                return "Good"
            elif score == 1:
                return "Fair"
            else:
                return "Poor"

        self.health_status = quark(
            plant_health,
            deps=[self.soil_moisture, self.temperature, self.light_level],
        )

        def status_emoji(get):
            """Get emoji based on plant status."""
            needs_water = get(self.needs_watering)
            health = get(self.health_status)

            if needs_water:
                return "🚰"
            elif health == "Excellent":
                return "🌿"
            elif health == "Good":
                return "🌱"
            elif health == "Fair":
                return "🍂"
            else:
                return "🥀"

        self.status_icon = quark(
            status_emoji, deps=[self.needs_watering, self.health_status]
        )

        # Setup monitoring
        self._setup_subscriptions()

    def _setup_subscriptions(self):
        """Setup monitoring subscriptions."""

        def on_watering_needed(q):
            if q.value:
                print(f"    💧 {self.plant_name} needs watering!")
            else:
                print(f"    ✅ {self.plant_name} has enough water")

        def on_health_change(q):
            print(f"    🏥 Health status: {q.value}")

        self.needs_watering.subscribe(on_watering_needed)
        self.health_status.subscribe(on_health_change)

    def update_sensors(self, moisture: float, temperature: float, light: float):
        """Update sensor readings."""
        self.soil_moisture.set(moisture)
        self.temperature.set(temperature)
        self.light_level.set(light)

    def water_plant(self):
        """Water the plant (simulated)."""
        if self.needs_watering.value:
            print(f"    💦 Watering {self.plant_name} for {self.watering_duration.value}s...")
            time.sleep(0.5)

            # Update moisture (simulated)
            new_moisture = min(100.0, self.soil_moisture.value + 30.0)
            self.soil_moisture.set(new_moisture)

            # Update history
            self.last_watered.set(time.strftime("%Y-%m-%d %H:%M:%S"))
            self.total_waterings.set(self.total_waterings.value + 1)

            print(f"    ✅ Watering complete! New moisture: {new_moisture:.1f}%")
        else:
            print(f"    ℹ️  {self.plant_name} doesn't need water right now")

    def display_status(self):
        """Display current plant status."""
        print(f"\n{self.status_icon.value} {self.plant_name.upper()}")
        print(f"  Soil Moisture: {self.soil_moisture.value:.1f}%")
        print(f"  Temperature:   {self.temperature.value:.1f}°C")
        print(f"  Light Level:   {self.light_level.value:.0f} lux")
        print(f"  Health:        {self.health_status.value}")
        print(f"  Last Watered:  {self.last_watered.value}")
        print(f"  Total Waters:  {self.total_waterings.value}")


def main():
    print("=== Smart Plant Monitor Example ===\n")

    # Create monitors for multiple plants
    tomato = PlantMonitor("Tomato")
    basil = PlantMonitor("Basil")

    print("Initial Status:")
    tomato.display_status()
    basil.display_status()

    print("\n--- Simulating Daily Care ---\n")

    # Day 1: Morning check
    print("☀️ Day 1 Morning:")
    tomato.update_sensors(moisture=65.0, temperature=22.0, light=600.0)
    basil.update_sensors(moisture=40.0, temperature=23.0, light=550.0)
    tomato.display_status()
    basil.display_status()

    # Day 1: Evening - soil drying out
    print("\n🌙 Day 1 Evening:")
    tomato.update_sensors(moisture=25.0, temperature=26.0, light=100.0)
    basil.update_sensors(moisture=22.0, temperature=25.0, light=80.0)
    print("\n🔍 Checking watering needs:")
    tomato.water_plant()
    basil.water_plant()

    # Day 2: Hot day
    print("\n☀️ Day 2 - Hot Day:")
    tomato.update_sensors(moisture=45.0, temperature=32.0, light=800.0)
    basil.update_sensors(moisture=38.0, temperature=31.0, light=750.0)
    print("\n🔍 Checking watering needs:")
    tomato.water_plant()
    basil.water_plant()

    # Day 3: Good conditions
    print("\n☀️ Day 3 - Optimal Conditions:")
    tomato.update_sensors(moisture=55.0, temperature=24.0, light=650.0)
    basil.update_sensors(moisture=50.0, temperature=23.0, light=600.0)
    tomato.display_status()
    basil.display_status()

    print("\n=== Example Complete ===")
    print("\n💡 Plant settings and history are stored in ./.statequark/")
    print("   Run the example again to see persistent watering history!")


if __name__ == "__main__":
    main()
