from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import unittest

from energy_meter_dsz15d_3x80a.config import ChannelConfig
from energy_meter_dsz15d_3x80a.database import PersistedState
from energy_meter_dsz15d_3x80a.service import PulseProcessor


class FakeRepository:
    def __init__(self, states: dict[str, PersistedState] | None = None) -> None:
        self.states = states or {}
        self.records: list[dict[str, object]] = []

    def load_state(self, channel: str) -> PersistedState:
        return self.states.get(channel, PersistedState(pulse_total=0, kwh_total=Decimal("0")))

    def record_pulse(self, **payload: object) -> None:
        self.records.append(payload)


class PulseProcessorTests(unittest.TestCase):
    def test_records_incremental_kwh(self) -> None:
        repository = FakeRepository()
        processor = PulseProcessor(
            channels=(
                ChannelConfig(name="s0", bcm_pin=17, impulses_per_kwh=1000, bounce_ms=30, edge="falling"),
            ),
            repository=repository,
        )

        timestamp = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        processor.process("s0", timestamp)
        processor.process("s0", timestamp)

        self.assertEqual(len(repository.records), 2)
        self.assertEqual(repository.records[0]["pulse_total"], 1)
        self.assertEqual(repository.records[1]["pulse_total"], 2)
        self.assertEqual(repository.records[1]["delta_kwh"], Decimal("0.001000"))
        self.assertEqual(repository.records[1]["kwh_total"], Decimal("0.002000"))

    def test_restores_last_persisted_state(self) -> None:
        repository = FakeRepository(
            {
                "s1": PersistedState(
                    pulse_total=42,
                    kwh_total=Decimal("10.500000"),
                )
            }
        )
        processor = PulseProcessor(
            channels=(
                ChannelConfig(name="s1", bcm_pin=27, impulses_per_kwh=2000, bounce_ms=30, edge="falling"),
            ),
            repository=repository,
        )

        processor.process("s1", datetime(2026, 1, 1, 13, 0, tzinfo=timezone.utc))

        self.assertEqual(repository.records[0]["pulse_total"], 43)
        self.assertEqual(repository.records[0]["delta_kwh"], Decimal("0.000500"))
        self.assertEqual(repository.records[0]["kwh_total"], Decimal("10.500500"))


if __name__ == "__main__":
    unittest.main()
