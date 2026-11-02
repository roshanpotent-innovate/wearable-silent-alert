from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import sys
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from alert_manager import AlertManager
from database import get_connection, initialize_database


manager = AlertManager(confirmation_timeout=15)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Wearable Silent Emergency Alert API",
    description="Simulation-only emergency alert prototype.",
    version="0.1.0",
    lifespan=lifespan,
)


class WearableReading(BaseModel):
    device_id: str = "WATCH-001"
    heart_rate_bpm: int | None = Field(default=None, ge=0, le=250)
    gesture_detected: bool = False
    acknowledged: bool | None = None
    explicit_sos: bool = False
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_accuracy_m: float | None = Field(default=None, ge=0)
    wearer_response: str | None = None


def store_incident(reading: dict, result: dict) -> str:
    incident_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO incidents (
                incident_id, created_at, device_id, alert_level,
                status, reason, heart_rate_bpm, latitude, longitude,
                location_accuracy_m, delivery_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                incident_id,
                created_at,
                reading.get("device_id", "WATCH-001"),
                result.get("alert_level", "UNKNOWN"),
                "OPEN",
                result.get("reason", "Emergency condition detected"),
                reading.get("heart_rate_bpm"),
                reading.get("latitude"),
                reading.get("longitude"),
                reading.get("location_accuracy_m"),
                "SIMULATED",
            ),
        )

    return incident_id


@app.get("/health")
def health():
    return {"status": "ok", "mode": "simulation_only"}


@app.post("/wearable/reading")
def receive_reading(reading: WearableReading):
    data = reading.model_dump()

    if data["wearer_response"] not in (None, "SAFE", "HELP"):
        raise HTTPException(
            status_code=422,
            detail="wearer_response must be SAFE, HELP, or null",
        )

    result = manager.process_reading(data)
    incident_id = None

    if result.get("action") == "SEND_EMERGENCY_ALERT":
        incident_id = store_incident(data, result)

    return {
        "device_id": data["device_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "result": result,
        "incident_id": incident_id,
        "delivery_status": "SIMULATED" if incident_id else None,
        "simulation_mode": True,
    }


@app.post("/wearable/response")
def receive_response(payload: dict):
    response = payload.get("response")

    if response not in ("SAFE", "HELP"):
        raise HTTPException(
            status_code=422,
            detail="response must be SAFE or HELP",
        )

    result = manager.process_reading({"wearer_response": response})
    incident_id = None

    if result.get("action") == "SEND_EMERGENCY_ALERT":
        incident_id = store_incident(
            {"device_id": "WATCH-001"},
            result,
        )

    return {
        "result": result,
        "incident_id": incident_id,
        "delivery_status": "SIMULATED" if incident_id else None,
        "simulation_mode": True,
    }


@app.get("/incidents")
def list_incidents():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM incidents ORDER BY created_at DESC"
        ).fetchall()

    return [dict(row) for row in rows]


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM incidents WHERE incident_id = ?",
            (incident_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    return dict(row)