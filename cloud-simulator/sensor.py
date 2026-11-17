"""Deterministic virtual GPIO weather sensors feeding the existing MariaDB schema."""
import math
import os
import random
import time
from datetime import datetime, timezone

import mysql.connector


def observation(tick, rng):
    phase = tick / 240.0
    temp = 12 + 5 * math.sin(phase) + rng.uniform(-0.3, 0.3)
    humidity = min(98, max(30, 67 - 15 * math.sin(phase) + rng.uniform(-2, 2)))
    wind = max(0, 11 + 8 * math.sin(tick / 31) + rng.uniform(-3, 3))
    gust = wind + rng.uniform(0, 12)
    direction = round((345 + 55 * math.sin(tick / 24) + rng.uniform(-8, 8)) % 360)
    rain = round(rng.uniform(0.01, 0.12), 2) if tick % 120 in range(20, 45) else 0
    uv = max(0, 5 * math.sin((tick % 5760) / 5760 * 2 * math.pi))
    dew = temp - (100 - humidity) / 5
    cardinals = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
    return (
        round(humidity, 1), round(temp, 1), round(temp - wind / 30, 1),
        round(dew, 1), round(1013 + 7 * math.sin(tick / 500), 1),
        rain, round(wind, 1), round(gust, 1), direction,
        cardinals[round(direction / 45) % 8], round(uv, 1),
        round(temp + 1.4, 1),
    )


SQL = """INSERT INTO dataentry
(HUMIDITY, AIR_TEMP, FEELS_LIKE, DEW_POINT, PRESSURE_SEA, RAINFALL,
 WIND_SPEED, WIND_GUST, WIND_DIRECTION, WIND_CARDINAL, UV_INDEX, TEMP_CASE)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""


def main():
    rng = random.Random(int(os.getenv("SENSOR_SEED", "42")))
    interval = max(1.0, float(os.getenv("SENSOR_INTERVAL_SECONDS", "15")))
    tick = 0
    while True:
        try:
            with mysql.connector.connect(
                host=os.getenv("DB_HOST", "database"),
                user="weather_user",
                password=os.getenv("DB_PASSWORD", "virtual-weather-only"),
                database="weather",
                connection_timeout=10,
                autocommit=True,
                time_zone="+00:00",
            ) as conn:
                with conn.cursor() as cursor:
                    values = observation(tick, rng)
                    cursor.execute(SQL, values)
                    print(f"{datetime.now(timezone.utc).isoformat()} sensor #{tick}: temp={values[1]}C wind={values[6]}km/h rain={values[5]}mm", flush=True)
            tick += 1
            time.sleep(interval)
        except (mysql.connector.Error, OSError) as exc:
            print(f"Sensor database error: {exc}; retrying", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
