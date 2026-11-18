"""Realistic, reproducible database-level weather sensor simulator.

RAINFALL represents millimetres observed during the current sample interval.
All timestamps and solar calculations use UTC; local solar hour is approximated
from configurable longitude. No external weather API or hardware is required.
"""
import math
import os
import random
import time
from datetime import datetime, timezone

import mysql.connector

SQL = """INSERT INTO dataentry
(HUMIDITY, AIR_TEMP, FEELS_LIKE, DEW_POINT, PRESSURE_SEA, RAINFALL,
 WIND_SPEED, WIND_GUST, WIND_DIRECTION, WIND_CARDINAL, UV_INDEX, TEMP_CASE)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

CARDINALS = ("N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
             "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW")


def clamp(value, low, high):
    return max(low, min(high, value))


def dew_point_c(temperature, humidity):
    """Magnus approximation, valid for typical ambient temperatures."""
    rh = clamp(humidity, 0.1, 100.0)
    gamma = math.log(rh / 100.0) + 17.625 * temperature / (243.04 + temperature)
    return 243.04 * gamma / (17.625 - gamma)


def apparent_temperature_c(temperature, humidity, wind_kph):
    """Canadian wind chill in its validity range; otherwise heat index or air temp."""
    if temperature <= 10 and wind_kph > 4.8:
        return (13.12 + 0.6215 * temperature
                - 11.37 * wind_kph ** 0.16
                + 0.3965 * temperature * wind_kph ** 0.16)
    if temperature >= 27 and humidity >= 40:
        f = temperature * 9 / 5 + 32
        r = humidity
        hi = (-42.379 + 2.04901523 * f + 10.14333127 * r
              - 0.22475541 * f * r - 0.00683783 * f * f
              - 0.05481717 * r * r + 0.00122874 * f * f * r
              + 0.00085282 * f * r * r - 0.00000199 * f * f * r * r)
        return (hi - 32) * 5 / 9
    return temperature


def solar_factor(now, longitude):
    """Approximate solar elevation/daylight, not an astronomical ephemeris."""
    day = now.timetuple().tm_yday
    latitude = math.radians(float(os.getenv("SIM_LATITUDE", "55.86")))
    declination = math.radians(23.44) * math.sin(2 * math.pi * (day - 81) / 365.2425)
    solar_hour = (now.hour + now.minute / 60 + now.second / 3600
                  + longitude / 15)
    hour_angle = math.radians(15 * (solar_hour - 12))
    elevation_sine = (math.sin(latitude) * math.sin(declination)
                      + math.cos(latitude) * math.cos(declination)
                      * math.cos(hour_angle))
    return clamp(elevation_sine, 0.0, 1.0)


class WeatherModel:
    def __init__(self, seed=42, interval=15):
        self.rng = random.Random(seed)
        self.interval = interval
        self.tick = 0
        self.wind_direction = 245.0
        self.wind_speed = 10.0
        self.pressure_offset = 0.0
        self.temperature_noise = 0.0
        self.humidity_noise = 0.0
        self.rain_remaining = 0
        self.rain_rate = 0.0
        self.cloud_cover = 0.3

    def sample(self, now):
        rng = self.rng
        day = now.timetuple().tm_yday
        solar = solar_factor(now, float(os.getenv("SIM_LONGITUDE", "-4.25")))
        # Northern-hemisphere seasonal baseline and daily solar warming.
        season = math.sin(2 * math.pi * (day - 172) / 365.2425)
        baseline = 9.5 + 6.8 * season
        self.temperature_noise = clamp(
            self.temperature_noise * 0.94 + rng.gauss(0, 0.09), -2.5, 2.5)
        self.humidity_noise = clamp(
            self.humidity_noise * 0.95 + rng.gauss(0, 0.4), -9, 9)
        self.pressure_offset = clamp(
            self.pressure_offset + rng.gauss(0, 0.025), -18, 18)

        if self.rain_remaining <= 0 and rng.random() < self.interval / (8 * 3600):
            self.rain_remaining = rng.randint(
                max(1, int(10 * 60 / self.interval)),
                max(2, int(90 * 60 / self.interval)))
            self.rain_rate = rng.uniform(0.3, 8.0)  # mm per hour
            self.cloud_cover = rng.uniform(0.75, 1.0)
        elif self.rain_remaining <= 0:
            self.cloud_cover = clamp(
                self.cloud_cover + rng.gauss(0, 0.012), 0.05, 0.95)

        raining = self.rain_remaining > 0
        if raining:
            self.rain_remaining -= 1
        sunlight = solar * (1 - 0.78 * self.cloud_cover)
        temp = baseline - 2.5 + 8.0 * sunlight + self.temperature_noise
        if raining:
            temp -= 0.8
        humidity = clamp(
            82 - 34 * sunlight + self.humidity_noise + (12 if raining else 0),
            28, 99)
        self.wind_speed = clamp(
            self.wind_speed * 0.91 + (10 + 6 * sunlight) * 0.09
            + rng.gauss(0, 1.1), 0, 65)
        self.wind_direction = (
            self.wind_direction + rng.gauss(0, 4.0)) % 360
        gust = self.wind_speed + max(0, rng.gauss(3.5, 2.2))
        rain_mm = (self.rain_rate * self.interval / 3600
                   * rng.uniform(0.65, 1.35)) if raining else 0.0
        # Stored schema supports 0.01 mm precision.
        rain_mm = round(rain_mm, 2)
        uv = clamp(9.0 * sunlight ** 1.4, 0, 11)
        dew = dew_point_c(temp, humidity)
        feels = apparent_temperature_c(temp, humidity, self.wind_speed)
        case_temp = temp + 0.5 + 5 * sunlight
        direction = int(round(self.wind_direction)) % 360
        cardinal = CARDINALS[int((direction + 11.25) // 22.5) % 16]
        self.tick += 1
        return (
            round(humidity, 1), round(temp, 1), round(feels, 1),
            round(dew, 1), round(1013.0 + self.pressure_offset, 1),
            rain_mm, round(self.wind_speed, 1), round(gust, 1),
            direction, cardinal, round(uv, 1), round(case_temp, 1)
        )


def main():
    interval = max(1.0, float(os.getenv("SENSOR_INTERVAL_SECONDS", "15")))
    model = WeatherModel(int(os.getenv("SENSOR_SEED", "42")), interval)
    print("Realistic DEMO sensor active; UTC clock; database-only output", flush=True)
    while True:
        started = time.monotonic()
        try:
            with mysql.connector.connect(
                host=os.getenv("DB_HOST", "database"),
                user="weather_user",
                password=os.getenv("DB_PASSWORD", "virtual-weather-only"),
                database="weather",
                connection_timeout=10,
                autocommit=True,
            ) as conn:
                with conn.cursor() as cursor:
                    now = datetime.now(timezone.utc)
                    values = model.sample(now)
                    cursor.execute(SQL, values)
                    print(
                        f"{now.isoformat()} sensor #{model.tick - 1}: "
                        f"temp={values[1]}C humidity={values[0]}% "
                        f"wind={values[6]}km/h gust={values[7]}km/h "
                        f"rain={values[5]}mm UV={values[10]} "
                        f"pressure={values[4]}hPa", flush=True)
        except (mysql.connector.Error, OSError) as exc:
            print(f"Sensor database error: {exc}; retrying", flush=True)
        time.sleep(max(0.5, interval - (time.monotonic() - started)))


if __name__ == "__main__":
    main()
