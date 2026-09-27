import unittest
from datetime import datetime, timedelta, timezone

from edge_telemetry.models import TelemetryReading
from edge_telemetry.storage import SQLiteTelemetryStore


class SQLiteTelemetryStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = SQLiteTelemetryStore()

    def tearDown(self) -> None:
        self.store.close()

    def test_persists_and_returns_latest_first(self) -> None:
        now = datetime.now(timezone.utc)
        older = TelemetryReading("a", "temperature", 20.0, "C", now - timedelta(seconds=1))
        newer = TelemetryReading("a", "temperature", 21.0, "C", now)
        self.store.write(older)
        self.store.write(newer)

        self.assertEqual(self.store.count(), 2)
        self.assertEqual([item.value for item in self.store.latest("temperature")], [21.0, 20.0])

    def test_latest_requires_positive_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            self.store.latest("temperature", 0)


if __name__ == "__main__":
    unittest.main()

