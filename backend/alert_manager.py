import time
from threading import RLock

from detection_engine import evaluate_reading


class AlertManager:
    def __init__(self, confirmation_timeout=15):
        self.confirmation_timeout = confirmation_timeout
        self.pending_alert = None
        self.lock = RLock()

    def process_reading(self, reading):
        with self.lock:
            if reading.get("explicit_sos") is True:
                self.pending_alert = None
                return self._emergency("Explicit SOS activated", reading)
            
            response = reading.get("wearer_response")

            if response == "HELP":
                original_reading = (
                    self.pending_alert["reading"].copy()
                    if self.pending_alert is not None
                    else {}
                )
                original_reading.update(reading)
                self.pending_alert = None
                return self._emergency("Wearer requested help", original_reading)

            if response == "SAFE":
                if self.pending_alert is not None:
                    self.pending_alert = None
                    return {
                        "alert_level": "NORMAL",
                        "action": "CANCEL_ALERT",
                        "reason": "Wearer confirmed safety",
                    }

                return {
                    "alert_level": "NORMAL",
                    "action": "CONTINUE_MONITORING",
                    "reason": "No pending alert",
                }

            if self.pending_alert is not None:
                elapsed = time.monotonic() - self.pending_alert["started_at"]

                if elapsed >= self.confirmation_timeout:
                    original_reading = self.pending_alert["reading"]
                    self.pending_alert = None
                    return self._emergency(
                        "Confirmation timeout expired",
                        original_reading,
                    )

                return {
                    "alert_level": "SUSPICIOUS",
                    "action": "WAITING_FOR_CONFIRMATION",
                    "seconds_remaining": max(
                        0,
                        round(self.confirmation_timeout - elapsed),
                    ),
                }

            result = evaluate_reading(reading)

            if result["action"] == "SEND_EMERGENCY_ALERT":
                return {**result, "_reading": reading}

            if result["action"] == "REQUEST_CONFIRMATION":
                self.pending_alert = {
                    "started_at": time.monotonic(),
                    "reason": result["reason"],
                    "reading": reading.copy(),
                }

                return {
                    "alert_level": "SUSPICIOUS",
                    "action": "REQUEST_CONFIRMATION",
                    "reason": result["reason"],
                    "timeout_seconds": self.confirmation_timeout,
                }

            return result

    def check_timeout(self):
        """Escalate a pending alert when its timer expires."""
        with self.lock:
            if self.pending_alert is None:
                return None

            elapsed = time.monotonic() - self.pending_alert["started_at"]

            if elapsed < self.confirmation_timeout:
                return {
                    "action": "WAITING_FOR_CONFIRMATION",
                    "seconds_remaining": max(
                        0,
                        round(self.confirmation_timeout - elapsed),
                    ),
                }

            original_reading = self.pending_alert["reading"]
            self.pending_alert = None

            return self._emergency(
                "Confirmation timeout expired",
                original_reading,
            )

    @staticmethod
    def _emergency(reason, reading=None):
        result = {
            "alert_level": "EMERGENCY",
            "action": "SEND_EMERGENCY_ALERT",
            "reason": reason,
        }

        if reading is not None:
            result["_reading"] = reading

        return result