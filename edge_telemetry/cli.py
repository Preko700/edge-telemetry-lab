from __future__ import annotations

import argparse
import asyncio

from .pipeline import TelemetryPipeline
from .simulator import SENSOR_RANGES, simulated_sensor
from .storage import SQLiteTelemetryStore


async def run(readings: int, interval: float, database: str) -> None:
    store = SQLiteTelemetryStore(database)
    pipeline = TelemetryPipeline(store)
    await pipeline.start()

    async def produce(sensor: str, seed: int) -> None:
        async for reading in simulated_sensor("greenhouse-01", sensor, readings, interval, seed):
            await pipeline.submit(reading)

    await asyncio.gather(
        *(produce(sensor, seed) for seed, sensor in enumerate(SENSOR_RANGES, start=1))
    )
    await pipeline.stop()

    metrics = pipeline.metrics
    print(
        f"processed={metrics.processed} persisted={metrics.persisted} "
        f"retries={metrics.retries} dropped={metrics.dropped} anomalies={metrics.anomalies}"
    )
    for sensor, summary in sorted(pipeline.analyzer.summaries().items()):
        print(
            f"{sensor}: count={summary.count} mean={summary.mean:.2f} "
            f"min={summary.minimum:.2f} max={summary.maximum:.2f}"
        )
    store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate a reliable edge telemetry pipeline")
    parser.add_argument("--readings", type=int, default=12, help="readings per sensor")
    parser.add_argument("--interval", type=float, default=0.01, help="seconds between readings")
    parser.add_argument("--database", default=":memory:", help="SQLite database path")
    args = parser.parse_args()
    if args.readings <= 0:
        parser.error("--readings must be positive")
    if args.interval < 0:
        parser.error("--interval cannot be negative")
    asyncio.run(run(args.readings, args.interval, args.database))


if __name__ == "__main__":
    main()

