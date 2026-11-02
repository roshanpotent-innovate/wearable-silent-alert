import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "incidents.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                device_id TEXT,
                alert_level TEXT NOT NULL,
                status TEXT NOT NULL,
                reason TEXT,
                heart_rate_bpm INTEGER,
                latitude REAL,
                longitude REAL,
                location_accuracy_m REAL,
                delivery_status TEXT NOT NULL DEFAULT 'SIMULATED'
            )
        """)