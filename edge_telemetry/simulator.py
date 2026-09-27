from __future__ import annotations

import asyncio
import random
from collections.abc import AsyncIterator

from .models import TelemetryReading


SENSOR_RANGES = {
    "temperature": (21.0, 27.0, "C"),
    "humidity": (40.0, 70.0, "%"),
    "light": (100.0, 1000.0, "lux"),
}


async def simulated_sensor(
    device_id: str,
    sensor: str,
    readings: int,
    interval_seconds: float,
    seed: int,
) -> AsyncIterator[TelemetryReading]:
    if sensor not in SENSOR_RANGES:
        raise ValueError(f"unknown sensor: {sensor}")
    low, high, unit = SENSOR_RANGES[sensor]
    random_source = random.Random(seed)
    for _ in range(readings):
        yield TelemetryReading.now(device_id, sensor, random_source.uniform(low, high), unit)
        await asyncio.sleep(interval_seconds)

