from enum import Enum


class AlertLevel(str, Enum):
    NORMAL = "NORMAL"
    SUSPICIOUS = "SUSPICIOUS"
    EMERGENCY = "EMERGENCY"


def evaluate_reading(reading: dict) -> dict:
    """
    Evaluate simulated wearable readings.
    This is prototype logic, not a validated medical or safety detector.
    """

    heart_rate = reading.get("heart_rate_bpm")
    gesture = reading.get("gesture_detected", False)
    acknowledged = reading.get("acknowledged")
    explicit_sos = reading.get("explicit_sos", False)

    # An explicit SOS bypasses the confirmation process.
    if explicit_sos:
        return {
            "alert_level": AlertLevel.EMERGENCY.value,
            "action": "SEND_EMERGENCY_ALERT",
            "reason": "Explicit SOS activated",
        }

    # Validate the heart-rate input if provided.
    if heart_rate is not None:
        if not isinstance(heart_rate, (int, float)) or isinstance(heart_rate, bool):
            return {
                "alert_level": AlertLevel.NORMAL.value,
                "action": "INVALID_READING",
                "reason": "Invalid heart-rate value",
            }

        if not 25 <= heart_rate <= 240:
            return {
                "alert_level": AlertLevel.NORMAL.value,
                "action": "INVALID_READING",
                "reason": "Heart-rate value outside configured limits",
            }

    # A missing heart-rate reading should not automatically cancel an SOS.
    # Without an SOS, flag incomplete data for monitoring.
    if heart_rate is None:
        if gesture:
            return {
                "alert_level": AlertLevel.SUSPICIOUS.value,
                "action": "REQUEST_CONFIRMATION",
                "reason": "Gesture detected; heart-rate data unavailable",
            }

        return {
            "alert_level": AlertLevel.NORMAL.value,
            "action": "CHECK_SENSOR",
            "reason": "Heart-rate data unavailable",
        }

    # A high heart rate alone does not prove an emergency.
    high_heart_rate = heart_rate >= 120

    if gesture and high_heart_rate:
        if acknowledged is False:
            return {
                "alert_level": AlertLevel.EMERGENCY.value,
                "action": "SEND_EMERGENCY_ALERT",
                "reason": "Suspicious gesture and elevated heart rate; no acknowledgement",
            }

        if acknowledged is True:
            return {
                "alert_level": AlertLevel.NORMAL.value,
                "action": "CONTINUE_MONITORING",
                "reason": "Wearer acknowledged the confirmation",
            }

        return {
            "alert_level": AlertLevel.SUSPICIOUS.value,
            "action": "REQUEST_CONFIRMATION",
            "reason": "Suspicious gesture and elevated heart rate",
        }

    if gesture:
        return {
            "alert_level": AlertLevel.SUSPICIOUS.value,
            "action": "REQUEST_CONFIRMATION",
            "reason": "Suspicious gesture detected",
        }

    return {
        "alert_level": AlertLevel.NORMAL.value,
        "action": "CONTINUE_MONITORING",
        "reason": (
            "Elevated heart rate; continue monitoring"
            if high_heart_rate
            else "No suspicious signals detected"
        ),
    }