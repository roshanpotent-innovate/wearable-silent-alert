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

def device_reading(device_id, heart_rate, latitude, longitude):
    return {
        "device_id": device_id,
        "heart_rate_bpm": heart_rate,
        "gesture_detected": True,
        "acknowledged": None,
        "explicit_sos": False,
        "latitude": latitude,
        "longitude": longitude,
        "location_accuracy_m": 10,
    }


def test_safe_response_only_cancels_its_own_device():
    manager = AlertManager(confirmation_timeout=15)

    # Both devices trigger suspicious events.
    manager.process_reading(
        device_reading("WATCH-A", 130, 13.0827, 80.2707)
    )
    manager.process_reading(
        device_reading("WATCH-B", 145, 13.0604, 80.2496)
    )

    assert "WATCH-A" in manager.pending_alerts
    assert "WATCH-B" in manager.pending_alerts

    # WATCH-A confirms that the wearer is safe.
    safe_result = manager.process_reading({
        "device_id": "WATCH-A",
        "wearer_response": "SAFE",
    })

    assert safe_result["action"] == "CANCEL_ALERT"

    # WATCH-B must still have its own pending alert.
    assert "WATCH-A" not in manager.pending_alerts
    assert "WATCH-B" in manager.pending_alerts

    # Confirm WATCH-B is still waiting for a response.
    waiting_result = manager.process_reading({
        "device_id": "WATCH-B",
    })

    assert waiting_result["action"] == "WAITING_FOR_CONFIRMATION"


def test_help_response_only_escalates_its_own_device():
    manager = AlertManager(confirmation_timeout=15)

    # Both devices trigger suspicious events.
    manager.process_reading(
        device_reading("WATCH-A", 130, 13.0827, 80.2707)
    )
    manager.process_reading(
        device_reading("WATCH-B", 145, 13.0604, 80.2496)
    )

    # WATCH-B requests help.
    result = manager.process_reading({
        "device_id": "WATCH-B",
        "wearer_response": "HELP",
    })

    assert result["action"] == "SEND_EMERGENCY_ALERT"
    assert result["alert_level"] == "EMERGENCY"

    # Verify the original WATCH-B sensor and GPS data are preserved.
    original_reading = result["_reading"]

    assert original_reading["device_id"] == "WATCH-B"
    assert original_reading["heart_rate_bpm"] == 145
    assert original_reading["latitude"] == 13.0604
    assert original_reading["longitude"] == 80.2496

    # WATCH-B's pending alert should be cleared.
    assert "WATCH-B" not in manager.pending_alerts

    # WATCH-A's pending alert must remain untouched.
    assert "WATCH-A" in manager.pending_alerts

    # WATCH-A can still independently confirm safety.
    safe_result = manager.process_reading({
        "device_id": "WATCH-A",
        "wearer_response": "SAFE",
    })

    assert safe_result["action"] == "CANCEL_ALERT"
    assert len(manager.pending_alerts) == 0

def test_timeout_escalates_only_once():
    manager = AlertManager(confirmation_timeout=0)

    first_result = manager.process_reading(
        device_reading("WATCH-TIMEOUT", 135, 13.0827, 80.2707)
    )

    assert first_result["action"] == "REQUEST_CONFIRMATION"

    # First timeout check should escalate the alert.
    expired_results = manager.check_timeouts()

    assert len(expired_results) == 1
    assert expired_results[0]["action"] == "SEND_EMERGENCY_ALERT"
    assert expired_results[0]["_reading"]["device_id"] == "WATCH-TIMEOUT"

    # A second check must not escalate the same alert again.
    second_check = manager.check_timeouts()

    assert second_check == []
    assert len(manager.pending_alerts) == 0


def test_multiple_devices_timeout_independently():
    manager = AlertManager(confirmation_timeout=0)

    manager.process_reading(
        device_reading("WATCH-TIMEOUT-A", 130, 13.0827, 80.2707)
    )

    manager.process_reading(
        device_reading("WATCH-TIMEOUT-B", 145, 13.0604, 80.2496)
    )

    assert len(manager.pending_alerts) == 2

    expired_results = manager.check_timeouts()

    assert len(expired_results) == 2

    expired_devices = {
        result["_reading"]["device_id"]
        for result in expired_results
    }

    assert expired_devices == {
        "WATCH-TIMEOUT-A",
        "WATCH-TIMEOUT-B",
    }

    # Verify each device's original sensor data is preserved.
    readings = {
        result["_reading"]["device_id"]: result["_reading"]
        for result in expired_results
    }

    assert readings["WATCH-TIMEOUT-A"]["heart_rate_bpm"] == 130
    assert readings["WATCH-TIMEOUT-A"]["latitude"] == 13.0827

    assert readings["WATCH-TIMEOUT-B"]["heart_rate_bpm"] == 145
    assert readings["WATCH-TIMEOUT-B"]["latitude"] == 13.0604

    assert len(manager.pending_alerts) == 0

    # Neither alert should be escalated again.
    assert manager.check_timeouts() == []