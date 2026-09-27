import asyncio
import unittest

from edge_telemetry.models import TelemetryReading
from edge_telemetry.pipeline import PipelineConfig, TelemetryPipeline
from edge_telemetry.storage import SQLiteTelemetryStore, TransientStorageError


class FlakyStore:
    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.writes: list[TelemetryReading] = []

    def write(self, reading: TelemetryReading) -> None:
        if self.failures:
            self.failures -= 1
            raise TransientStorageError("temporary lock")
        self.writes.append(reading)


class TelemetryPipelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_processes_reading_end_to_end(self) -> None:
        store = SQLiteTelemetryStore()
        pipeline = TelemetryPipeline(store)
        await pipeline.start()
        accepted = await pipeline.submit(
            TelemetryReading.now("device-1", "temperature", 24.5, "C")
        )
        await pipeline.stop()

        self.assertTrue(accepted)
        self.assertEqual(store.count(), 1)
        self.assertEqual(pipeline.metrics.processed, 1)
        self.assertEqual(pipeline.metrics.persisted, 1)
        store.close()

    async def test_retries_transient_storage_error(self) -> None:
        store = FlakyStore(failures=2)
        config = PipelineConfig(max_retries=2, initial_backoff_seconds=0)
        pipeline = TelemetryPipeline(store, config)
        await pipeline.start()
        await pipeline.submit(TelemetryReading.now("device-1", "humidity", 55.0, "%"))
        await pipeline.stop()

        self.assertEqual(len(store.writes), 1)
        self.assertEqual(pipeline.metrics.retries, 2)
        self.assertEqual(pipeline.metrics.persisted, 1)

    async def test_submit_before_start_fails(self) -> None:
        pipeline = TelemetryPipeline(FlakyStore(failures=0))
        with self.assertRaisesRegex(RuntimeError, "not started"):
            await pipeline.submit(TelemetryReading.now("device-1", "light", 400.0, "lux"))


if __name__ == "__main__":
    unittest.main()

