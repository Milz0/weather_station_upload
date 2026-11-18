"""Unit tests for the realistic virtual sensor (no MariaDB required)."""
import unittest
from datetime import datetime, timezone

from sensor import WeatherModel, apparent_temperature_c, dew_point_c, solar_factor


class SensorTests(unittest.TestCase):
    def test_night_uv_zero(self):
        now = datetime(2026, 11, 18, 0, 0, tzinfo=timezone.utc)
        model = WeatherModel()
        self.assertEqual(model.sample(now)[10], 0)

    def test_summer_midday_brighter_than_midnight(self):
        midday = datetime(2026, 6, 21, 12, tzinfo=timezone.utc)
        midnight = datetime(2026, 6, 21, 0, tzinfo=timezone.utc)
        self.assertGreater(solar_factor(midday, -4.25), solar_factor(midnight, -4.25))

    def test_dew_point_never_exceeds_temperature(self):
        for rh in (20, 50, 80, 100):
            self.assertLessEqual(dew_point_c(18, rh), 18.000001)

    def test_wind_chill(self):
        self.assertLess(apparent_temperature_c(2, 60, 25), 2)

    def test_all_schema_fields_and_ranges(self):
        model = WeatherModel(seed=42)
        now = datetime(2026, 7, 18, 12, tzinfo=timezone.utc)
        for _ in range(100):
            row = model.sample(now)
            self.assertEqual(len(row), 12)
            self.assertTrue(0 <= row[0] <= 100)
            self.assertTrue(0 <= row[8] < 360)
            self.assertTrue(0 <= row[10] <= 11)
            self.assertTrue(0 <= row[5])
            self.assertLessEqual(len(row[9]), 3)

    def test_repeatable_with_same_clock_and_seed(self):
        now = datetime(2026, 5, 18, 12, tzinfo=timezone.utc)
        self.assertEqual(WeatherModel(42).sample(now), WeatherModel(42).sample(now))


if __name__ == "__main__":
    unittest.main()
