from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .config import DatabaseConfig


@dataclass(frozen=True, slots=True)
class PersistedState:
    pulse_total: int
    kwh_total: Decimal


class MariaDbPulseRepository:
    def __init__(self, connection: object, table: str) -> None:
        self._connection = connection
        self._table = table
        self._create_table_sql = f"""
CREATE TABLE IF NOT EXISTS `{table}` (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    channel VARCHAR(64) NOT NULL,
    captured_at DATETIME(6) NOT NULL,
    pulse_total BIGINT UNSIGNED NOT NULL,
    delta_pulses INT UNSIGNED NOT NULL,
    kwh_total DECIMAL(18, 6) NOT NULL,
    delta_kwh DECIMAL(12, 6) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_{table}_channel_captured_at (channel, captured_at),
    KEY idx_{table}_captured_at (captured_at)
)
"""
        self._select_state_sql = (
            f"SELECT pulse_total, kwh_total FROM `{table}` "
            "WHERE channel = ? ORDER BY captured_at DESC, id DESC LIMIT 1"
        )
        self._insert_sql = (
            f"INSERT INTO `{table}` "
            "(channel, captured_at, pulse_total, delta_pulses, kwh_total, delta_kwh) "
            "VALUES (?, ?, ?, ?, ?, ?)"
        )

    @classmethod
    def connect(cls, config: DatabaseConfig) -> "MariaDbPulseRepository":
        import mariadb

        connection = mariadb.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database,
            connect_timeout=config.connect_timeout,
            autocommit=True,
        )
        repository = cls(connection, config.table)
        repository.initialize_schema()
        return repository

    def initialize_schema(self) -> None:
        cursor = self._connection.cursor()
        try:
            cursor.execute(self._create_table_sql)
        finally:
            cursor.close()

    def load_state(self, channel: str) -> PersistedState:
        cursor = self._connection.cursor()
        try:
            cursor.execute(self._select_state_sql, (channel,))
            row = cursor.fetchone()
        finally:
            cursor.close()

        if row is None:
            return PersistedState(pulse_total=0, kwh_total=Decimal("0"))

        pulse_total, kwh_total = row
        return PersistedState(pulse_total=int(pulse_total), kwh_total=Decimal(str(kwh_total)))

    def record_pulse(
        self,
        *,
        channel: str,
        captured_at: datetime,
        pulse_total: int,
        delta_pulses: int,
        kwh_total: Decimal,
        delta_kwh: Decimal,
    ) -> None:
        cursor = self._connection.cursor()
        try:
            cursor.execute(
                self._insert_sql,
                (
                    channel,
                    captured_at,
                    pulse_total,
                    delta_pulses,
                    str(kwh_total),
                    str(delta_kwh),
                ),
            )
        finally:
            cursor.close()

    def close(self) -> None:
        self._connection.close()
