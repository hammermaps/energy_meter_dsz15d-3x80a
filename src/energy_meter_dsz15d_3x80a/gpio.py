from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from .config import ChannelConfig


class RpiGpioPulseSource:
    def __init__(
        self,
        channels: tuple[ChannelConfig, ...],
        on_pulse: Callable[[str, datetime], None],
    ) -> None:
        self._channels = channels
        self._on_pulse = on_pulse
        self._gpio = None

    def start(self) -> None:
        try:
            import RPi.GPIO as gpio
        except ImportError as exc:
            raise RuntimeError(
                "RPi.GPIO ist nicht installiert. Auf Raspberry Pi bitte 'python3-rpi.gpio' installieren."
            ) from exc

        gpio.setwarnings(False)
        gpio.setmode(gpio.BCM)

        edge_map = {
            "falling": gpio.FALLING,
            "rising": gpio.RISING,
            "both": gpio.BOTH,
        }

        for channel in self._channels:
            gpio.setup(channel.bcm_pin, gpio.IN, pull_up_down=gpio.PUD_UP)
            gpio.add_event_detect(
                channel.bcm_pin,
                edge_map[channel.edge],
                callback=self._make_callback(channel.name),
                bouncetime=channel.bounce_ms,
            )

        self._gpio = gpio

    def stop(self) -> None:
        if self._gpio is None:
            return

        for channel in self._channels:
            self._gpio.remove_event_detect(channel.bcm_pin)
        self._gpio.cleanup()
        self._gpio = None

    def _make_callback(self, channel_name: str) -> Callable[[int], None]:
        def callback(_: int) -> None:
            self._on_pulse(channel_name, datetime.now(timezone.utc))

        return callback
