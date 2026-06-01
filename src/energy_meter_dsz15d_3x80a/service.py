from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import logging
from threading import Lock

from .config import ChannelConfig
from .database import PersistedState


@dataclass(slots=True)
class ChannelRuntimeState:
    pulse_total: int
    kwh_total: Decimal


class PulseProcessor:
    def __init__(
        self,
        *,
        channels: tuple[ChannelConfig, ...],
        repository: object,
        logger: logging.Logger | None = None,
    ) -> None:
        self._repository = repository
        self._logger = logger or logging.getLogger(__name__)
        self._lock = Lock()
        self._increments = {
            channel.name: (Decimal("1") / Decimal(channel.impulses_per_kwh)).quantize(Decimal("0.000001"))
            for channel in channels
        }
        self._states = {
            channel.name: self._to_runtime_state(repository.load_state(channel.name))
            for channel in channels
        }

    def process(self, channel: str, captured_at: datetime | None = None) -> None:
        if channel not in self._states:
            raise KeyError(f"Unbekannter Kanal: {channel}")

        event_time = captured_at or datetime.now(timezone.utc)
        delta_kwh = self._increments[channel]

        with self._lock:
            state = self._states[channel]
            state.pulse_total += 1
            state.kwh_total += delta_kwh
            pulse_total = state.pulse_total
            kwh_total = state.kwh_total

            self._repository.record_pulse(
                channel=channel,
                captured_at=event_time,
                pulse_total=pulse_total,
                delta_pulses=1,
                kwh_total=kwh_total,
                delta_kwh=delta_kwh,
            )

        self._logger.debug(
            "Impuls erfasst: channel=%s pulse_total=%s kwh_total=%s timestamp=%s",
            channel,
            pulse_total,
            kwh_total,
            event_time.isoformat(),
        )

    @staticmethod
    def _to_runtime_state(state: PersistedState) -> ChannelRuntimeState:
        return ChannelRuntimeState(
            pulse_total=state.pulse_total,
            kwh_total=state.kwh_total,
        )
