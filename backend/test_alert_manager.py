from alert_manager import AlertManager


def suspicious_reading():
    return {
        "heart_rate_bpm": 85,
        "gesture_detected": True,
        "acknowledged": None,
        "explicit_sos": False,
    }


def test_suspicious_event_requests_confirmation():
    manager = AlertManager(confirmation_timeout=15)

    result = manager.process_reading(suspicious_reading())

    assert result["action"] == "REQUEST_CONFIRMATION"


def test_safe_response_cancels_pending_alert():
    manager = AlertManager(confirmation_timeout=15)

    manager.process_reading(suspicious_reading())

    result = manager.process_reading({"wearer_response": "SAFE"})

    assert result["action"] == "CANCEL_ALERT"
    assert manager.pending_alert is None


def test_help_response_escalates_immediately():
    manager = AlertManager()

    result = manager.process_reading({"wearer_response": "HELP"})

    assert result["action"] == "SEND_EMERGENCY_ALERT"


def test_explicit_sos_escalates_immediately():
    manager = AlertManager()

    result = manager.process_reading({"explicit_sos": True})

    assert result["action"] == "SEND_EMERGENCY_ALERT"


def test_timeout_escalates_without_new_sensor_readings():
    manager = AlertManager(confirmation_timeout=0)

    manager.process_reading(suspicious_reading())

    result = manager.check_timeout()

    assert result["action"] == "SEND_EMERGENCY_ALERT"
    assert manager.pending_alert is None


def test_invalid_response_does_not_cancel_alert():
    manager = AlertManager()

    manager.process_reading(suspicious_reading())

    result = manager.process_reading({"wearer_response": "MAYBE"})

    assert manager.pending_alert is not None
    assert result["action"] == "WAITING_FOR_CONFIRMATION"