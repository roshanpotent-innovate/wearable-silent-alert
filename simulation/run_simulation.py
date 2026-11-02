import sys
import time
import json
from pathlib import Path

# Allow importing the detection engine from the backend folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from detection_engine import evaluate_reading
from wearable_simulator import generate_reading


def main():
    print("\n=== WEARABLE EMERGENCY ALERT SIMULATION ===")
    print("Simulation only. No real sensors or police connection.\n")

    try:
        while True:
            # Generate simulated wearable data.
            reading = generate_reading()

            # Evaluate the data using our detection engine.
            result = evaluate_reading(reading)

            print("-" * 55)
            print("WEARABLE DATA:")
            print(json.dumps(reading, indent=2))

            print("\nDETECTION RESULT:")
            print(json.dumps(result, indent=2))

            if result["action"] == "SEND_EMERGENCY_ALERT":
                print("\n!!! SIMULATED EMERGENCY ALERT !!!")

            time.sleep(3)

    except KeyboardInterrupt:
        print("\nSimulation stopped.")


if __name__ == "__main__":
    main()