import time
from threading import RLock

from detection_engine import evaluate_reading


class AlertManager:
    def __init__(self, confirmation_timeout=15):
        self.confirmation_timeout = confirmation_timeout

        # Each device maintains its own pending confirmation.
        self.pending_alerts = {}

        self.lock = RLock()

    @property
    def pending_alert(self):
        """
        Backward-compatible access for existing tests and older code.

        Returns the default device's pending alert when present.
        If exactly one other device has a pending alert, returns that.
        Returns None when there are no pending alerts or multiple
        non-default devices have pending alerts.
        """
        with self.lock:
            if "WATCH-001" in self.pending_alerts:
                return self.pending_alerts["WATCH-001"]

            if len(self.pending_alerts) == 1:
                return next(iter(self.pending_alerts.values()))

            return None

    def process_reading(self, reading):
        with self.lock:
            reading = reading.copy()
            device_id = reading.get("device_id", "WATCH-001")

            # Ensure every reading has a device identifier.
            reading["device_id"] = device_id

            # Explicit SOS bypasses confirmation.
            if reading.get("explicit_sos") is True:
                self.pending_alerts.pop(device_id, None)

                return self._emergency(
                    "Explicit SOS activated",
                    reading,
                )

            response = reading.get("wearer_response")
            pending = self.pending_alerts.get(device_id)

            # HELP escalates this device's pending alert.
            if response == "HELP":
                if pending is not None:
                    # Preserve the original triggering sensor data.
                    original_reading = pending["reading"].copy()
                    self.pending_alerts.pop(device_id, None)

                    return self._emergency(
                        "Wearer requested help",
                        original_reading,
                    )

                # HELP without a pending alert is still an explicit
                # request for assistance.
                return self._emergency(
                    "Wearer requested help",
                    reading,
                )

            # SAFE cancels only this device's pending alert.
            if response == "SAFE":
                if pending is not None:
                    self.pending_alerts.pop(device_id, None)

                    return {
                        "alert_level": "NORMAL",
                        "action": "CANCEL_ALERT",
                        "reason": "Wearer confirmed safety",
                    }

                return {
                    "alert_level": "NORMAL",
                    "action": "CONTINUE_MONITORING",
                    "reason": "No pending alert for this device",
                }

            # Check the pending alert for this device only.
            if pending is not None:
                elapsed = time.monotonic() - pending["started_at"]

                if elapsed >= self.confirmation_timeout:
                    original_reading = pending["reading"].copy()
                    self.pending_alerts.pop(device_id, None)

                    return self._emergency(
                        "Confirmation timeout expired",
                        original_reading,
                    )

                return {
                    "alert_level": "SUSPICIOUS",
                    "action": "WAITING_FOR_CONFIRMATION",
                    "reason": pending["reason"],
                    "seconds_remaining": max(
                        0,
                        round(self.confirmation_timeout - elapsed),
                    ),
                }

            # No pending alert: evaluate this device's new reading.
            result = evaluate_reading(reading)

            if result["action"] == "SEND_EMERGENCY_ALERT":
                return {
                    **result,
                    "_reading": reading.copy(),
                }

            if result["action"] == "REQUEST_CONFIRMATION":
                self.pending_alerts[device_id] = {
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

    def check_timeouts(self):
        """
        Return all pending alerts whose confirmation time has expired.

        Each expired alert is removed before being returned, preventing
        the timeout monitor from repeatedly escalating the same alert.
        """
        expired_results = []

        with self.lock:
            now = time.monotonic()

            for device_id, pending in list(self.pending_alerts.items()):
                elapsed = now - pending["started_at"]

                if elapsed >= self.confirmation_timeout:
                    original_reading = pending["reading"].copy()

                    self.pending_alerts.pop(device_id, None)

                    expired_results.append(
                        self._emergency(
                            "Confirmation timeout expired",
                            original_reading,
                        )
                    )

        return expired_results

    def check_timeout(self):
        """
        Backward-compatible single-result timeout check.

        New backend code should use check_timeouts() so that all devices
        are checked during every monitoring cycle.
        """
        results = self.check_timeouts()

        if results:
            return results[0]

        with self.lock:
            if not self.pending_alerts:
                return None

            now = time.monotonic()

            earliest = min(
                self.pending_alerts.values(),
                key=lambda alert: alert["started_at"],
            )

            elapsed = now - earliest["started_at"]

            return {
                "action": "WAITING_FOR_CONFIRMATION",
                "seconds_remaining": max(
                    0,
                    round(self.confirmation_timeout - elapsed),
                ),
            }

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