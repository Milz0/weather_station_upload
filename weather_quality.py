"""Weather observation validation and meteorological calculations."""
from datetime import datetime, timezone
from math import atan2, cos, degrees, radians, sin, isfinite


def circular_mean_degrees(directions, weights=None):
    """Return circular mean in degrees; None if undefined or no valid samples."""
    values = list(directions)
    if weights is None:
        weights = [1.0] * len(values)
    else:
        weights = list(weights)
    if len(values) != len(weights):
        raise ValueError("directions and weights must have equal lengths")
    x = y = 0.0
    for direction, weight in zip(values, weights):
        if direction is None or weight is None:
            continue
        angle, weight = float(direction), float(weight)
        if not isfinite(angle) or not isfinite(weight) or weight < 0:
            continue
        x += weight * cos(radians(angle))
        y += weight * sin(radians(angle))
    if abs(x) < 1e-10 and abs(y) < 1e-10:
        return None
    return degrees(atan2(y, x)) % 360.0


def validate_observation(data, max_age_seconds=600, now=None):
    """Reject missing, stale, future-dated, or physically invalid observations."""
    if not isinstance(data, dict):
        raise ValueError("Missing observation")
    timestamp = data.get("timestamp")
    if not isinstance(timestamp, datetime):
        raise ValueError("Observation timestamp is missing")
    if timestamp.tzinfo is None:
        # Database CREATED is interpreted in the configured local system timezone.
        timestamp = timestamp.astimezone()
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.astimezone()
    age = (now - timestamp).total_seconds()
    if age > max_age_seconds or age < -120:
        raise ValueError("Observation is stale or future-dated")
    ranges = {
        "temperature": (-90, 65),
        "humidity": (0, 100),
        "pressure_sea": (800, 1100),
        "wind_speed_10min": (0, 450),
        "wind_gust_10min": (0, 450),
        "daily_rain": (0, 2000),
        "hourly_rain": (0, 500),
    }
    for key, (lower, upper) in ranges.items():
        value = data.get(key)
        if value is None or not isfinite(float(value)) or not lower <= float(value) <= upper:
            raise ValueError("Invalid observation field: " + key)
    return data
