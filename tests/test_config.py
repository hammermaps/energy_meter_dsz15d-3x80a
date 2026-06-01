from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from energy_meter_dsz15d_3x80a.config import load_config


VALID_CONFIG = """
[database]
host = "127.0.0.1"
user = "meter"
password = "secret"
database = "energy_meter"

[[channels]]
name = "s0"
bcm_pin = 17
impulses_per_kwh = 1000
"""


class LoadConfigTests(unittest.TestCase):
    def _write_config(self, content: str) -> str:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        path = Path(tmpdir.name) / "config.toml"
        path.write_text(content, encoding="utf-8")
        return str(path)

    def test_loads_defaults(self) -> None:
        config = load_config(self._write_config(VALID_CONFIG))

        self.assertEqual(config.database.port, 3306)
        self.assertEqual(config.database.table, "meter_pulses")
        self.assertEqual(config.channels[0].edge, "falling")
        self.assertEqual(config.channels[0].bounce_ms, 30)

    def test_rejects_duplicate_gpio_pins(self) -> None:
        content = VALID_CONFIG + """
[[channels]]
name = "s1"
bcm_pin = 17
"""

        with self.assertRaisesRegex(ValueError, "Doppelter GPIO-Pin"):
            load_config(self._write_config(content))


if __name__ == "__main__":
    unittest.main()
