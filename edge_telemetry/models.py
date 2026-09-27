from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite


@dataclass(frozen=True, slots=True)
class TelemetryReading:
    device_id: str
    sensor: str
    value: float
    unit: str
    observed_at: datetime

    def __post_init__(self) -> None:
        if not self.device_id.strip():
            raise ValueError("device_id cannot be empty")
        if not self.sensor.strip():
            raise ValueError("sensor cannot be empty")
        if not self.unit.strip():
            raise ValueError("unit cannot be empty")
        if not isfinite(self.value):
            raise ValueError("value must be finite")
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")

    @classmethod
    def now(cls, device_id: str, sensor: str, value: float, unit: str) -> "TelemetryReading":
        return cls(device_id, sensor, value, unit, datetime.now(timezone.utc))

