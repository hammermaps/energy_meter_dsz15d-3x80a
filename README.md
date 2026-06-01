# energy_meter_dsz15d-3x80a

Python-3.14-Anwendung zur Erfassung von `S0`/`S1`-Impulsen eines **Eltako DSZ15D-3x80A** auf einem Raspberry Pi mit Raspberry Pi OS. Jeder Impuls wird in `kWh` umgerechnet und mit Zeitstempel in eine **MariaDB** geschrieben, damit eine nachgelagerte PHP-Anwendung Verbraeuche pro Stunde, Tag, Woche oder Jahr aggregieren kann.

## Enthaltene Bausteine

- Python-Dienst unter `src/energy_meter_dsz15d_3x80a`
- Beispielkonfiguration unter `config/energy-meter.example.toml`
- `systemd`-Unit unter `deploy/energy-meter.service`
- Hardwarebeschreibung, Verschaltungsplaene und Materialliste unter `docs/hardware.md`

## Datenbankschema

Die Anwendung legt die Tabelle beim Start automatisch an:

```sql
CREATE TABLE meter_pulses (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    channel VARCHAR(64) NOT NULL,
    captured_at DATETIME(6) NOT NULL,
    pulse_total BIGINT UNSIGNED NOT NULL,
    delta_pulses INT UNSIGNED NOT NULL,
    kwh_total DECIMAL(18, 6) NOT NULL,
    delta_kwh DECIMAL(12, 6) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_meter_pulses_channel_captured_at (channel, captured_at),
    KEY idx_meter_pulses_captured_at (captured_at)
);
```

Fuer die spaetere PHP-Auswertung reicht in der Regel:

```sql
SELECT
    channel,
    DATE_FORMAT(captured_at, '%Y-%m-%d %H:00:00') AS hour_bucket,
    SUM(delta_kwh) AS kwh
FROM meter_pulses
GROUP BY channel, hour_bucket
ORDER BY hour_bucket;
```

## Installation auf Raspberry Pi OS

```bash
sudo apt update
sudo apt install -y python3.14 python3.14-venv python3-rpi.gpio libmariadb-dev build-essential
sudo mkdir -p /opt/energy-meter /etc/energy-meter
sudo cp -r . /opt/energy-meter
cd /opt/energy-meter
python3.14 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install .
sudo cp config/energy-meter.example.toml /etc/energy-meter/config.toml
sudo nano /etc/energy-meter/config.toml
sudo cp deploy/energy-meter.service /etc/systemd/system/energy-meter.service
sudo systemctl daemon-reload
sudo systemctl enable --now energy-meter.service
sudo systemctl status energy-meter.service
```

## Konfiguration

```toml
[database]
host = "127.0.0.1"
port = 3306
user = "energy_meter"
password = "BITTE-AENDERN"
database = "energy_meter"
table = "meter_pulses"
connect_timeout = 5

[[channels]]
name = "s0"
bcm_pin = 17
impulses_per_kwh = 1000
bounce_ms = 30
edge = "falling"

[[channels]]
name = "s1"
bcm_pin = 27
impulses_per_kwh = 1000
bounce_ms = 30
edge = "falling"
```

## Anwendung pruefen

Konfiguration pruefen:

```bash
PYTHONPATH=src python3 -m energy_meter_dsz15d_3x80a --config config/energy-meter.example.toml --check-config
```

Danach startet `systemd` die eigentliche Erfassung und ueberwacht den Prozess per `Restart=always`.

## Hardware

Die Verdrahtung, Schutzbeschaltung und Materialliste stehen in [`docs/hardware.md`](docs/hardware.md).
