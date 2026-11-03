import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from main import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_normal_reading_does_not_create_incident():
    with TestClient(app) as client:
        response = client.post(
            "/wearable/reading",
            json={
                "device_id": "TEST-WATCH",
                "heart_rate_bpm": 75,
                "gesture_detected": False,
                "explicit_sos": False,
            },
        )
        incidents = client.get("/incidents")

    assert response.status_code == 200
    assert response.json()["simulation_mode"] is True
    assert response.json()["incident_id"] is None
    assert incidents.status_code == 200


def test_invalid_wearer_response_is_rejected():
    with TestClient(app) as client:
        response = client.post(
            "/wearable/response",
            json={"response": "MAYBE"},
        )

    assert response.status_code == 422


def test_explicit_sos_creates_incident():
    with TestClient(app) as client:
        response = client.post(
            "/wearable/reading",
            json={
                "device_id": "TEST-SOS",
                "heart_rate_bpm": 80,
                "explicit_sos": True,
                "latitude": 13.0827,
                "longitude": 80.2707,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["action"] == "SEND_EMERGENCY_ALERT"
    assert body["incident_id"] is not None
    assert body["delivery_status"] == "SIMULATED"

def test_emergency_incident_is_created_without_gps():
    with TestClient(app) as client:
        response = client.post(
            "/wearable/reading",
            json={
                "device_id": "TEST-NO-GPS",
                "heart_rate_bpm": 80,
                "gesture_detected": False,
                "explicit_sos": True,
            },
        )

        assert response.status_code == 200

        body = response.json()
        incident_id = body["incident_id"]

        assert incident_id is not None
        assert body["delivery_status"] == "SIMULATED"

        incidents_response = client.get("/incidents")
        incidents = incidents_response.json()

        incident = next(
            item for item in incidents
            if item["incident_id"] == incident_id
        )

    assert incident["device_id"] == "TEST-NO-GPS"
    assert incident["alert_level"] == "EMERGENCY"
    assert incident["heart_rate_bpm"] == 80
    assert incident["latitude"] is None
    assert incident["longitude"] is None
    assert incident["delivery_status"] == "SIMULATED"