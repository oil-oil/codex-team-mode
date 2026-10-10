from __future__ import annotations

import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills" / "team-mode" / "scripts" / "current_model.py"
SPEC = importlib.util.spec_from_file_location("current_model", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
current_model = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(current_model)


class ParseTimeTests(unittest.TestCase):
    def test_parse_time_rejects_non_string_and_empty_values(self) -> None:
        for value in (None, 0, False, b"2024-01-01T00:00:00", ""):
            with self.subTest(value=value):
                self.assertIsNone(current_model.parse_time(value))

    def test_parse_time_normalizes_naive_iso_timestamp_to_utc(self) -> None:
        self.assertEqual(
            current_model.parse_time("2024-02-29T23:59:59"),
            datetime(2024, 2, 29, 23, 59, 59, tzinfo=timezone.utc),
        )

    def test_parse_time_preserves_explicit_timezone_and_z_suffix(self) -> None:
        self.assertEqual(
            current_model.parse_time("2024-01-01T00:00:00+05:30"),
            datetime(2024, 1, 1, tzinfo=timezone(timedelta(hours=5, minutes=30))),
        )
        self.assertEqual(
            current_model.parse_time("2024-01-01T00:00:00Z"),
            datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

    def test_parse_time_rejects_invalid_iso_strings(self) -> None:
        for value in ("not-a-date", "2023-02-29T00:00:00", "2024-13-01T00:00:00"):
            with self.subTest(value=value):
                self.assertIsNone(current_model.parse_time(value))


if __name__ == "__main__":
    unittest.main()
