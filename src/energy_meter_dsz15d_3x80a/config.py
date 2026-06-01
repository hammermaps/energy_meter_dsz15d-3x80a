from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tomllib


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    table: str
    connect_timeout: int


@dataclass(frozen=True, slots=True)
class ChannelConfig:
    name: str
    bcm_pin: int
    impulses_per_kwh: int
    bounce_ms: int
    edge: str


@dataclass(frozen=True, slots=True)
class AppConfig:
    database: DatabaseConfig
    channels: tuple[ChannelConfig, ...]


def load_config(path: str | Path) -> AppConfig:
    raw = tomllib.loads(Path(path).read_text(encoding="utf-8"))

    database_section = raw.get("database")
    if not isinstance(database_section, dict):
        raise ValueError("Konfigurationsabschnitt [database] fehlt.")

    table = str(database_section.get("table", "meter_pulses"))
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
        raise ValueError("database.table darf nur Buchstaben, Zahlen und Unterstriche enthalten.")
    if len(table) > 40:
        raise ValueError("database.table darf maximal 40 Zeichen lang sein.")

    database = DatabaseConfig(
        _require_text(database_section, "host"),
        _require_int(database_section, "port", default=3306, minimum=1),
        _require_text(database_section, "user"),
        _require_text(database_section, "password"),
        _require_text(database_section, "database"),
        table,
        _require_int(database_section, "connect_timeout", default=5, minimum=1),
    )

    raw_channels = raw.get("channels")
    if not isinstance(raw_channels, list) or not raw_channels:
        raise ValueError("Mindestens ein [[channels]] Eintrag ist erforderlich.")

    channels: list[ChannelConfig] = []
    seen_names: set[str] = set()
    seen_pins: set[int] = set()

    for item in raw_channels:
        if not isinstance(item, dict):
            raise ValueError("Jeder [[channels]] Eintrag muss ein Objekt sein.")

        channel = ChannelConfig(
            name=_require_text(item, "name"),
            bcm_pin=_require_int(item, "bcm_pin", minimum=0),
            impulses_per_kwh=_require_int(item, "impulses_per_kwh", default=1000, minimum=1),
            bounce_ms=_require_int(item, "bounce_ms", default=30, minimum=0),
            edge=_require_edge(item.get("edge", "falling")),
        )

        if channel.name in seen_names:
            raise ValueError(f"Doppelter Kanalname: {channel.name}")
        if channel.bcm_pin in seen_pins:
            raise ValueError(f"Doppelter GPIO-Pin: BCM {channel.bcm_pin}")

        seen_names.add(channel.name)
        seen_pins.add(channel.bcm_pin)
        channels.append(channel)

    return AppConfig(database=database, channels=tuple(channels))


def _require_text(section: dict[str, object], key: str) -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} muss als nicht-leerer Text gesetzt sein.")
    return value.strip()


def _require_int(
    section: dict[str, object],
    key: str,
    *,
    default: int | None = None,
    minimum: int | None = None,
) -> int:
    value = section.get(key, default)
    if not isinstance(value, int):
        raise ValueError(f"{key} muss eine Ganzzahl sein.")
    if minimum is not None and value < minimum:
        raise ValueError(f"{key} muss >= {minimum} sein.")
    return value


def _require_edge(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("edge muss ein Textwert sein.")
    normalized = value.strip().lower()
    if normalized not in {"falling", "rising", "both"}:
        raise ValueError("edge muss 'falling', 'rising' oder 'both' sein.")
    return normalized
