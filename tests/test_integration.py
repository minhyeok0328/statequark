"""Integration tests with complex real-world scenarios."""

import asyncio
import time

import pytest

from statequark import quark


def test_iot_device_monitoring_system():
    """Test complete IoT device monitoring system."""
    # Device sensors
    temperature = quark(22.0)
    humidity = quark(45.0)
    battery_level = quark(85.0)

    # System state tracking
    alerts = []
    device_events = []

    def system_status(get):
        temp = get(temperature)
        hum = get(humidity)
        battery = get(battery_level)

        if battery < 20:
            return "critical"
        elif temp > 30 or hum > 80:
            return "warning"
        else:
            return "normal"

    def device_health(get):
        temp = get(temperature)
        hum = get(humidity)
        battery = get(battery_level)

        # Health score calculation
        temp_score = 100 if 20 <= temp <= 25 else max(0, 100 - abs(temp - 22.5) * 4)
        hum_score = 100 if 40 <= hum <= 60 else max(0, 100 - abs(hum - 50) * 2)
        battery_score = battery

        return round((temp_score + hum_score + battery_score) / 3)

    def alert_callback(q):
        if q.value in ["critical", "warning"]:
            alerts.append(f"Alert: {q.value} at {time.strftime('%H:%M:%S')}")

    def health_callback(q):
        device_events.append(f"Health: {q.value}%")

    status = quark(system_status, deps=[temperature, humidity, battery_level])
    health = quark(device_health, deps=[temperature, humidity, battery_level])

    status.subscribe(alert_callback)
    health.subscribe(health_callback)

    # Initial state
    assert status.value == "normal"
    initial_health = health.value
    assert initial_health > 80

    # Simulate temperature spike
    temperature.set(35.0)
    assert status.value == "warning"
    assert len(alerts) == 1

    # Simulate battery drain
    battery_level.set(15.0)
    assert status.value == "critical"
    assert len(alerts) == 2

    # Verify health tracking
    assert len(device_events) >= 2  # Should have tracked health changes


def test_smart_thermostat_system():
    """Test smart thermostat control system."""
    # Sensors and settings
    current_temp = quark(20.0)
    target_temp = quark(22.0)
    outdoor_temp = quark(15.0)
    occupancy = quark(True)

    # System state
    heating_commands = []
    energy_usage = []

    def heating_needed(get):
        current = get(current_temp)
        target = get(target_temp)
        occupied = get(occupancy)

        if not occupied:
            # Lower target when not occupied
            target = target - 2

        return current < target - 0.5

    def energy_efficiency(get):
        current = get(current_temp)
        outdoor = get(outdoor_temp)
        heating = get(heating_system)

        temp_diff = abs(current - outdoor)
        if heating:
            efficiency = max(20, 100 - temp_diff * 2)
        else:
            efficiency = 100

        return round(efficiency)

    def heating_callback(q):
        action = "ON" if q.value else "OFF"
        heating_commands.append(f"Heating: {action}")

    def efficiency_callback(q):
        energy_usage.append(q.value)

    heating_system = quark(heating_needed, deps=[current_temp, target_temp, occupancy])
    efficiency = quark(
        energy_efficiency, deps=[current_temp, outdoor_temp, heating_system]
    )

    heating_system.subscribe(heating_callback)
    efficiency.subscribe(efficiency_callback)

    # Test heating control - initial state doesn't trigger callback
    assert heating_system.value is True  # Should be heating (20 < 21.5)

    # Trigger first callback by changing temperature
    current_temp.set(18.0)  # Force heating on
    assert heating_system.value is True
    assert len(heating_commands) == 1

    # Simulate room heating up
    current_temp.set(22.5)
    assert heating_system.value is False  # Should stop heating
    assert len(heating_commands) == 2

    # Test occupancy effect
    occupancy.set(False)
    current_temp.set(
        19.5
    )  # Lower than occupied target but within unoccupied range
    assert heating_system.value is False  # Should not heat (19.5 >= 20-0.5)


def test_greenhouse_automation_system():
    """Test automated greenhouse management system."""
    # Environmental sensors - start with low light to test grow lights
    soil_moisture = quark(60.0)
    air_temp = quark(24.0)
    light_level = quark(200)  # Low light level to trigger grow lights

    # Control systems
    irrigation_log = []
    ventilation_log = []
    lighting_log = []

    def irrigation_needed(get):
        moisture = get(soil_moisture)
        temp = get(air_temp)

        # Need water if soil is dry or temperature is high
        return moisture < 40 or (temp > 28 and moisture < 60)

    def ventilation_needed(get):
        temp = get(air_temp)
        return temp > 26

    def grow_lights_needed(get):
        light = get(light_level)
        temp = get(air_temp)

        # Need lights if natural light is low and temperature allows
        return light < 300 and temp < 30

    def irrigation_callback(q):
        if q.value:
            irrigation_log.append("Start irrigation")
        else:
            irrigation_log.append("Stop irrigation")

    def ventilation_callback(q):
        if q.value:
            ventilation_log.append("Start ventilation")
        else:
            ventilation_log.append("Stop ventilation")

    def lighting_callback(q):
        if q.value:
            lighting_log.append("Turn on grow lights")
        else:
            lighting_log.append("Turn off grow lights")

    irrigation = quark(irrigation_needed, deps=[soil_moisture, air_temp])
    ventilation = quark(ventilation_needed, deps=[air_temp])
    grow_lights = quark(grow_lights_needed, deps=[light_level, air_temp])

    irrigation.subscribe(irrigation_callback)
    ventilation.subscribe(ventilation_callback)
    grow_lights.subscribe(lighting_callback)

    # Initial state
    assert irrigation.value is False  # Soil moisture OK
    assert ventilation.value is False  # Temperature OK
    assert grow_lights.value is True  # Light level low (200 < 300)

    # Simulate drought conditions
    soil_moisture.set(30.0)
    assert irrigation.value is True
    assert "Start irrigation" in irrigation_log

    # Simulate hot day
    air_temp.set(32.0)
    assert ventilation.value is True
    assert grow_lights.value is False  # Too hot for lights
    assert "Start ventilation" in ventilation_log
    assert "Turn off grow lights" in lighting_log

    # Simulate evening (cooler, darker)
    air_temp.set(20.0)
    light_level.set(100)
    assert ventilation.value is False
    assert grow_lights.value is True


@pytest.mark.asyncio
async def test_async_sensor_network():
    """Test async sensor network with data aggregation."""
    # Multiple sensors
    sensors = {
        "sensor_1": quark({"temp": 22.0, "status": "online"}),
        "sensor_2": quark({"temp": 23.5, "status": "online"}),
        "sensor_3": quark({"temp": 21.8, "status": "online"}),
    }

    network_events = []

    def network_status(get):
        online_count = 0
        total_temp = 0
        temp_count = 0

        for sensor in sensors.values():
            data = get(sensor)
            if data["status"] == "online":
                online_count += 1
                total_temp += data["temp"]
                temp_count += 1

        avg_temp = total_temp / temp_count if temp_count > 0 else 0

        return {
            "online_sensors": online_count,
            "average_temp": round(avg_temp, 1),
            "network_health": "good" if online_count >= 2 else "degraded",
        }

    def network_callback(q):
        status = q.value
        network_events.append(
            f"Network: {status['online_sensors']} sensors, "
            f"avg temp: {status['average_temp']}°C, "
            f"health: {status['network_health']}"
        )

    network = quark(network_status, deps=list(sensors.values()))
    network.subscribe(network_callback)

    # Test initial state
    initial_status = network.value
    assert initial_status["online_sensors"] == 3
    assert initial_status["average_temp"] == 22.4
    assert initial_status["network_health"] == "good"

    # Simulate sensor updates
    await sensors["sensor_1"].set_async({"temp": 25.0, "status": "online"})
    await sensors["sensor_2"].set_async({"temp": 24.0, "status": "offline"})

    # Wait a bit for async processing
    await asyncio.sleep(0.01)

    final_status = network.value
    assert final_status["online_sensors"] == 2
    assert final_status["network_health"] == "good"  # Still >= 2 sensors

    # Take another sensor offline
    await sensors["sensor_3"].set_async({"temp": 21.8, "status": "offline"})
    await asyncio.sleep(0.01)

    degraded_status = network.value
    assert degraded_status["online_sensors"] == 1
    assert degraded_status["network_health"] == "degraded"


def test_production_line_monitoring():
    """Test production line monitoring system."""
    # Production metrics - start with high temperature to test efficiency alerts
    items_produced = quark(0)
    defect_count = quark(0)
    machine_temp = quark(70.0)  # High temperature to trigger efficiency alert
    production_rate = quark(100)  # items per hour

    # System metrics
    quality_reports = []
    alerts = []

    def quality_percentage(get):
        produced = get(items_produced)
        defects = get(defect_count)

        if produced == 0:
            return 100.0

        quality = ((produced - defects) / produced) * 100
        return round(quality, 2)

    def production_efficiency(get):
        actual_rate = get(production_rate)
        temp = get(machine_temp)

        # Efficiency drops with high temperature
        temp_factor = 1.0 if temp <= 50 else max(0.5, 1.0 - (temp - 50) * 0.02)
        efficiency = actual_rate * temp_factor

        return round(efficiency, 1)

    def quality_callback(q):
        quality = q.value
        quality_reports.append(f"Quality: {quality}%")

        if quality < 95:
            alerts.append(f"Quality alert: {quality}%")

    def efficiency_callback(q):
        efficiency = q.value
        if efficiency < 80:
            alerts.append(f"Efficiency alert: {efficiency}")

    quality = quark(quality_percentage, deps=[items_produced, defect_count])
    efficiency = quark(production_efficiency, deps=[production_rate, machine_temp])

    quality.subscribe(quality_callback)
    efficiency.subscribe(efficiency_callback)

    # Check initial efficiency alert due to high temperature
    initial_efficiency = efficiency.value
    assert initial_efficiency < 80  # Should be low due to high temperature (70°C)

    # Trigger efficiency callback by changing temperature
    machine_temp.set(75.0)  # Even higher temperature
    assert any("Efficiency alert" in alert for alert in alerts)

    # Simulate production
    items_produced.set(100)
    defect_count.set(2)

    assert quality.value == 98.0
    assert "Quality: 98.0%" in quality_reports

    # Simulate quality issues
    defect_count.set(8)  # 8 defects out of 100
    assert quality.value == 92.0
    assert any("Quality alert: 92.0%" in alert for alert in alerts)

    # Reset temperature to normal to test efficiency improvement
    machine_temp.set(45.0)
    current_efficiency = efficiency.value
    assert current_efficiency == 100.0  # Should be back to normal
