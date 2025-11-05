#!/usr/bin/env python3
"""
Persistent Storage Example

Demonstrates how to use storage utilities to maintain state across
device reboots. Perfect for IoT devices that need to remember their
configuration and state.
"""

import time
from statequark import quark_with_storage, StorageType, quark_with_reset


def main():
    print("=== Persistent Storage Example ===\n")

    # Example 1: Session Storage (temporary, cleared on reboot)
    print("1. Session Storage (temporary):")
    print("   Stored in: /tmp/statequark/")

    temp_counter = quark_with_storage(
        "temp_counter", initial_value=0, storage_type=StorageType.SESSION
    )

    print(f"   Current counter value: {temp_counter.value}")
    print("   Incrementing counter...")

    for i in range(3):
        temp_counter.set(temp_counter.value + 1)
        print(f"   Counter: {temp_counter.value}")
        time.sleep(0.3)

    print("   💡 This value will be lost on system reboot\n")

    # Example 2: Local Storage (persistent)
    print("2. Local Storage (persistent):")
    print("   Stored in: ./.statequark/")

    device_config = quark_with_storage(
        "device_config",
        initial_value={"name": "RaspberryPi-001", "mode": "auto", "threshold": 25.0},
        storage_type=StorageType.LOCAL,
    )

    print(f"   Current config: {device_config.value}")
    print("   Updating config...")

    new_config = device_config.value.copy()
    new_config["threshold"] = 28.5
    new_config["mode"] = "manual"
    device_config.set(new_config)

    print(f"   Updated config: {device_config.value}")
    print("   💡 This value persists across program restarts\n")

    # Example 3: Custom Storage Path
    print("3. Custom Storage Path:")

    sensor_calibration = quark_with_storage(
        "sensor_cal",
        initial_value=1.0,
        storage_type=StorageType.LOCAL,
        base_path="/tmp/custom_storage",
    )

    print(f"   Stored in: /tmp/custom_storage/.statequark/")
    print(f"   Calibration value: {sensor_calibration.value}")

    sensor_calibration.set(1.05)
    print(f"   Updated calibration: {sensor_calibration.value}\n")

    # Example 4: Quark with Reset
    print("4. Quark with Reset (factory reset capability):")

    temperature_offset, reset_offset = quark_with_reset(0.0)
    print(f"   Initial offset: {temperature_offset.value}")

    temperature_offset.set(2.5)
    print(f"   Modified offset: {temperature_offset.value}")

    print("   Performing factory reset...")
    reset_offset.set(None)
    print(f"   After reset: {temperature_offset.value}")

    print("\n=== Example Complete ===")
    print("\n💡 Storage locations:")
    print("   - Session: /tmp/statequark/")
    print("   - Local: ./.statequark/")
    print("   - Custom: /tmp/custom_storage/.statequark/")


if __name__ == "__main__":
    main()
