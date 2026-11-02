from detection_engine import evaluate_reading


def test_explicit_sos():
    result = evaluate_reading({
        "explicit_sos": True,
        "heart_rate_bpm": 80,
        "gesture_detected": False,
        "acknowledged": True,
    })
    assert result["action"] == "SEND_EMERGENCY_ALERT"


def test_high_heart_rate_alone():
    result = evaluate_reading({
        "explicit_sos": False,
        "heart_rate_bpm": 140,
        "gesture_detected": False,
        "acknowledged": True,
    })
    assert result["action"] == "CONTINUE_MONITORING"


def test_gesture_requests_confirmation():
    result = evaluate_reading({
        "explicit_sos": False,
        "heart_rate_bpm": 85,
        "gesture_detected": True,
        "acknowledged": None,
    })
    assert result["action"] == "REQUEST_CONFIRMATION"


def test_gesture_and_high_heart_rate_without_acknowledgement():
    result = evaluate_reading({
        "explicit_sos": False,
        "heart_rate_bpm": 140,
        "gesture_detected": True,
        "acknowledged": False,
    })
    assert result["action"] == "SEND_EMERGENCY_ALERT"


def test_invalid_heart_rate():
    result = evaluate_reading({
        "explicit_sos": False,
        "heart_rate_bpm": -5,
        "gesture_detected": False,
        "acknowledged": True,
    })
    assert result["action"] == "INVALID_READING"