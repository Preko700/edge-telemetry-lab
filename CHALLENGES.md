# Extension challenges

Each challenge is intentionally small enough for a focused pull request and specific enough to verify with tests.

## 1. Dead-letter queue

Persist readings that still fail after all retries.

Acceptance criteria:

- stores the reading, error type, error message, and timestamp;
- provides a CLI command to list unresolved failures;
- includes tests for write and read behavior.

## 2. Time-bucket rollups

Add one-minute aggregates for each sensor.

Acceptance criteria:

- calculates count, minimum, maximum, and mean;
- handles out-of-order timestamps;
- does not double-count a reading when rerun.

## 3. WebSocket gateway

Stream accepted readings to connected clients.

Acceptance criteria:

- slow clients cannot block persistence;
- disconnected clients are removed safely;
- integration tests cover connect, receive, and disconnect.

## 4. Hardware adapter

Implement a source for one real sensor or microcontroller protocol.

Acceptance criteria:

- keeps hardware-specific code behind the `TelemetrySource` protocol;
- documents wiring and protocol details;
- includes a fake adapter for CI tests.

## 5. Observability

Export pipeline metrics in Prometheus text format.

Acceptance criteria:

- exposes processed, persisted, retried, and dropped counters;
- reports queue depth and processing latency;
- includes a test snapshot of the output format.

