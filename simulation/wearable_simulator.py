import random
import time
import json
from datetime import datetime, timezone


def generate_reading():
    """Generate simulated wearable sensor data."""

    scenarios = [
        {
            "scenario": "normal",
            "heart_rate": random.randint(65, 95),
            "gesture_detected": False,
            "acknowledged": True,
        },
        {
            "scenario": "normal_movement",
            "heart_rate": random.randint(80, 110),
            "gesture_detected": True,
            "acknowledged": True,
        },
        {
            "scenario": "elevated_heart_rate",
            "heart_rate": random.randint(115, 145),
            "gesture_detected": False,
            "acknowledged": True,
        },
        {
            "scenario": "possible_distress",
            "heart_rate": random.randint(120, 155),
            "gesture_detected": True,
            "acknowledged": False,
        },
        {
            "scenario": "explicit_sos",
            "heart_rate": random.randint(80, 150),
            "gesture_detected": False,
            "acknowledged": False,
        },
    ]

    reading = random.choice(scenarios)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "device_id": "BAND-001",
        "heart_rate_bpm": reading["heart_rate"],
        "gesture_detected": reading["gesture_detected"],
        "acknowledged": reading["acknowledged"],
        "explicit_sos": reading["scenario"] == "explicit_sos",
        "scenario": reading["scenario"],
        "simulation_mode": True,
    }


def main():
    print("=" * 50)
    print(" WEARABLE SILENT EMERGENCY ALERT BAND")
    print(" Virtual Wearable Simulator")
    print(" SIMULATION ONLY — NO REAL SENSORS")
    print("=" * 50)

    try:
        while True:
            reading = generate_reading()

            print("\nNew sensor reading:")
            print(json.dumps(reading, indent=4))

            time.sleep(3)

    except KeyboardInterrupt:
        print("\nSimulator stopped.")


if __name__ == "__main__":
    main()