from __future__ import annotations

import argparse
from datetime import datetime, timezone
import logging
import signal
import sys
from threading import Event

from .config import load_config
from .database import MariaDbPulseRepository
from .gpio import RpiGpioPulseSource
from .service import PulseProcessor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="energy-meter-dsz15d-3x80a",
        description="Erfasst S0/S1 Impulse am Raspberry Pi und speichert diese in MariaDB.",
    )
    parser.add_argument(
        "--config",
        default="/etc/energy-meter/config.toml",
        help="Pfad zur TOML-Konfiguration (Standard: /etc/energy-meter/config.toml)",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Konfiguration nur validieren und danach beenden.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Log-Level (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    config = load_config(args.config)
    if args.check_config:
        channel_summary = ", ".join(f"{channel.name}@BCM{channel.bcm_pin}" for channel in config.channels)
        print(f"Konfiguration OK: {channel_summary}")
        return 0

    repository = MariaDbPulseRepository.connect(config.database)
    processor = PulseProcessor(channels=config.channels, repository=repository, logger=logging.getLogger("meter"))
    source = RpiGpioPulseSource(config.channels, processor.process)
    stop_event = Event()

    def request_stop(_: int, __: object) -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    try:
        source.start()
        logging.getLogger("meter").info("Starte Impuls-Erfassung fuer %s Kanaele.", len(config.channels))
        while not stop_event.wait(1):
            pass
    finally:
        source.stop()
        repository.close()
        logging.getLogger("meter").info(
            "Impuls-Erfassung beendet um %s.",
            datetime.now(timezone.utc).isoformat(),
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
