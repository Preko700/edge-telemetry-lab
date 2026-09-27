import unittest
from datetime import datetime, timezone

from edge_telemetry.models import TelemetryReading


class TelemetryReadingTests(unittest.TestCase):
    def test_rejects_naive_timestamp(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            TelemetryReading("device-1", "temperature", 22.0, "C", datetime.now())

    def test_rejects_non_finite_value(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            TelemetryReading("device-1", "temperature", float("nan"), "C", datetime.now(timezone.utc))


if __name__ == "__main__":
    unittest.main()

