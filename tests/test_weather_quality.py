"""Run with python3 -m unittest discover -s tests -v."""
import unittest
from datetime import datetime, timedelta, timezone

from weather_quality import circular_mean_degrees, validate_observation


class WeatherQualityTests(unittest.TestCase):
    def test_north_wraparound(self):
        self.assertAlmostEqual(circular_mean_degrees([350, 10]), 0)

    def test_opposing_directions_are_undefined(self):
        self.assertIsNone(circular_mean_degrees([90, 270]))

    def test_empty_directions(self):
        self.assertIsNone(circular_mean_degrees([]))

    def test_weighted_mean(self):
        self.assertAlmostEqual(circular_mean_degrees([0, 90], [3, 1]), 18.43494882, places=5)

    def test_reject_stale_observation(self):
        data = self.observation()
        data["timestamp"] -= timedelta(minutes=30)
        with self.assertRaises(ValueError):
            validate_observation(data)

    def test_reject_invalid_humidity(self):
        data = self.observation()
        data["humidity"] = 110
        with self.assertRaises(ValueError):
            validate_observation(data)

    def test_valid_observation(self):
        self.assertIsNotNone(validate_observation(self.observation()))

    @staticmethod
    def observation():
        return {
            "timestamp": datetime.now(timezone.utc),
            "temperature": 12,
            "humidity": 65,
            "pressure_sea": 1013,
            "wind_speed_10min": 10,
            "wind_gust_10min": 15,
            "daily_rain": 1,
            "hourly_rain": 0.5,
        }


if __name__ == "__main__":
    unittest.main()
