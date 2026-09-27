from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol

from .analytics import RollingAnalyzer
from .models import TelemetryReading
from .storage import TransientStorageError


class TelemetryStore(Protocol):
    def write(self, reading: TelemetryReading) -> None: ...


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    queue_capacity: int = 64
    enqueue_timeout_seconds: float = 0.25
    max_retries: int = 3
    initial_backoff_seconds: float = 0.01


@dataclass(slots=True)
class PipelineMetrics:
    processed: int = 0
    persisted: int = 0
    retries: int = 0
    dropped: int = 0
    anomalies: int = 0


class TelemetryPipeline:
    def __init__(
        self,
        store: TelemetryStore,
        config: PipelineConfig | None = None,
        analyzer: RollingAnalyzer | None = None,
    ) -> None:
        self.config = config or PipelineConfig()
        if self.config.queue_capacity <= 0:
            raise ValueError("queue_capacity must be positive")
        self.store = store
        self.analyzer = analyzer or RollingAnalyzer()
        self.metrics = PipelineMetrics()
        self._queue: asyncio.Queue[TelemetryReading | None] = asyncio.Queue(
            maxsize=self.config.queue_capacity
        )
        self._consumer: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._consumer is not None:
            raise RuntimeError("pipeline already started")
        self._consumer = asyncio.create_task(self._consume())

    async def submit(self, reading: TelemetryReading) -> bool:
        if self._consumer is None:
            raise RuntimeError("pipeline is not started")
        try:
            await asyncio.wait_for(
                self._queue.put(reading), timeout=self.config.enqueue_timeout_seconds
            )
            return True
        except TimeoutError:
            self.metrics.dropped += 1
            return False

    async def stop(self) -> None:
        if self._consumer is None:
            return
        await self._queue.put(None)
        await self._consumer
        self._consumer = None

    async def _consume(self) -> None:
        while True:
            reading = await self._queue.get()
            try:
                if reading is None:
                    return
                self.metrics.processed += 1
                if self.analyzer.add(reading):
                    self.metrics.anomalies += 1
                await self._persist_with_retry(reading)
            finally:
                self._queue.task_done()

    async def _persist_with_retry(self, reading: TelemetryReading) -> None:
        for attempt in range(self.config.max_retries + 1):
            try:
                await asyncio.to_thread(self.store.write, reading)
                self.metrics.persisted += 1
                return
            except TransientStorageError:
                if attempt >= self.config.max_retries:
                    raise
                self.metrics.retries += 1
                delay = self.config.initial_backoff_seconds * (2**attempt)
                await asyncio.sleep(delay)

