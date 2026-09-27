from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from statistics import fmean, pstdev

from .models import TelemetryReading


@dataclass(frozen=True, slots=True)
class SensorSummary:
    count: int
    minimum: float
    maximum: float
    mean: float


class RollingAnalyzer:
    def __init__(self, window_size: int = 20, anomaly_z_score: float = 3.0) -> None:
        if window_size < 2:
            raise ValueError("window_size must be at least 2")
        self._values: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=window_size))
        self._anomaly_z_score = anomaly_z_score

    def add(self, reading: TelemetryReading) -> bool:
        values = self._values[reading.sensor]
        is_anomaly = False
        if len(values) >= 5:
            mean = fmean(values)
            deviation = pstdev(values)
            if deviation > 0:
                is_anomaly = abs(reading.value - mean) / deviation >= self._anomaly_z_score
        values.append(reading.value)
        return is_anomaly

    def summaries(self) -> dict[str, SensorSummary]:
        result: dict[str, SensorSummary] = {}
        for sensor, values in self._values.items():
            if values:
                result[sensor] = SensorSummary(
                    count=len(values),
                    minimum=min(values),
                    maximum=max(values),
                    mean=fmean(values),
                )
        return result

