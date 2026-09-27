from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock

from .models import TelemetryReading


class TransientStorageError(RuntimeError):
    """A temporary sink error that the pipeline may retry."""


class SQLiteTelemetryStore:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self._connection = sqlite3.connect(str(path), check_same_thread=False)
        self._lock = Lock()
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    sensor TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    observed_at TEXT NOT NULL
                )
                """
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_telemetry_sensor_time "
                "ON telemetry(sensor, observed_at DESC)"
            )

    def write(self, reading: TelemetryReading) -> None:
        try:
            with self._lock, self._connection:
                self._connection.execute(
                    "INSERT INTO telemetry(device_id, sensor, value, unit, observed_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        reading.device_id,
                        reading.sensor,
                        reading.value,
                        reading.unit,
                        reading.observed_at.isoformat(),
                    ),
                )
        except sqlite3.OperationalError as exc:
            raise TransientStorageError(str(exc)) from exc

    def count(self) -> int:
        with self._lock:
            row = self._connection.execute("SELECT COUNT(*) FROM telemetry").fetchone()
        return int(row[0])

    def latest(self, sensor: str, limit: int = 10) -> list[TelemetryReading]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self._lock:
            rows = self._connection.execute(
                "SELECT device_id, sensor, value, unit, observed_at "
                "FROM telemetry WHERE sensor = ? ORDER BY observed_at DESC LIMIT ?",
                (sensor, limit),
            ).fetchall()
        from datetime import datetime

        return [
            TelemetryReading(row[0], row[1], float(row[2]), row[3], datetime.fromisoformat(row[4]))
            for row in rows
        ]

    def close(self) -> None:
        self._connection.close()

