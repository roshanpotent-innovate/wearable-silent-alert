import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Literal
import sys
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from alert_manager import AlertManager
from database import get_connection, initialize_database


manager = AlertManager(confirmation_timeout=15)
async def monitor_confirmation_timeout():
    while True:
        result = manager.check_timeout()

        if result and result.get("action") == "SEND_EMERGENCY_ALERT":
            reading = result.pop("_reading", {})
            store_incident(reading, result)

        await asyncio.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    timer_task = asyncio.create_task(monitor_confirmation_timeout())

    try:
        yield
    finally:
        timer_task.cancel()
        with suppress(asyncio.CancelledError):
            await timer_task


app = FastAPI(
    title="Wearable Silent Emergency Alert API",
    description="Simulation-only emergency alert prototype.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
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

class IncidentStatusUpdate(BaseModel):
    status: Literal[
        "OPEN",
        "ACKNOWLEDGED",
        "DISPATCHED_SIMULATED",
        "CLOSED",
    ]

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
        incident_reading = result.pop("_reading", data)
        incident_id = store_incident(incident_reading, result)

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

@app.post("/incidents/{incident_id}/status")
def update_incident_status(
    incident_id: str,
    update: IncidentStatusUpdate,
):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT incident_id FROM incidents WHERE incident_id = ?",
            (incident_id,),
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found",
            )

        connection.execute(
            "UPDATE incidents SET status = ? WHERE incident_id = ?",
            (update.status, incident_id),
        )

        updated = connection.execute(
            "SELECT * FROM incidents WHERE incident_id = ?",
            (incident_id,),
        ).fetchone()

    return {
        "incident": dict(updated),
        "simulation_mode": True,
        "message": (
            "Status updated locally. No real emergency service was contacted."
        ),
    }

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