"""Read-only authenticated weather API for the Docker simulator."""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import mysql.connector
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Weather Station Gateway", version="1.2", docs_url=None, redoc_url=None, openapi_url=None)
TOKEN = os.getenv("API_TOKEN", "")
INSTALLATION = os.getenv("INSTALLATION_ID", "ws01")
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
DB_HOST = os.getenv("DB_HOST", "database")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
if not TOKEN or len(TOKEN) < 32:
    raise RuntimeError("API_TOKEN must be set to a random secret of at least 32 characters")
if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", INSTALLATION):
    raise RuntimeError("Invalid INSTALLATION_ID")
if RATE_LIMIT < 1:
    raise RuntimeError("RATE_LIMIT_PER_MINUTE must be positive")

_hits = defaultdict(deque)
_lock = threading.Lock()
COLUMNS = ("HUMIDITY", "AIR_TEMP", "FEELS_LIKE", "DEW_POINT", "PRESSURE_SEA",
           "RAINFALL", "WIND_SPEED", "WIND_GUST", "WIND_DIRECTION",
           "WIND_CARDINAL", "UV_INDEX", "TEMP_CASE")
FIELDS = ("humidity", "airTemp", "feelsLike", "dewPoint", "pressureSea",
          "rainfall", "windSpeed", "windGust", "windDirection",
          "windCardinal", "uvIndex", "tempCase")


def error(status, code, message, field=None, headers=None):
    detail = {"code": code, "message": message}
    if field is not None:
        detail["field"] = field
    return JSONResponse(
        status_code=status,
        content={"error": detail, "requestId": secrets.token_hex(8)},
        headers=headers,
    )


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    if isinstance(exc.detail, dict):
        return error(exc.status_code, exc.detail.get("code", "HTTP_ERROR"),
                     exc.detail.get("message", "Request failed"),
                     headers=exc.headers)
    return error(exc.status_code, "HTTP_ERROR", str(exc.detail), headers=exc.headers)


@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    return error(503, "SERVICE_UNAVAILABLE", "Weather gateway temporarily unavailable")


def authorize(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer ") or not hmac.compare_digest(
        authorization[7:].encode(), TOKEN.encode()
    ):
        raise HTTPException(401, {"code": "UNAUTHORIZED", "message": "Invalid bearer token"})
    # Rate limit per credential; one credential is configured for this deployment.
    now = time.monotonic()
    with _lock:
        hits = _hits["api"]
        while hits and now - hits[0] >= 60:
            hits.popleft()
        if len(hits) >= RATE_LIMIT:
            retry = max(1, int(61 - (now - hits[0])))
            raise HTTPException(
                429, {"code": "RATE_LIMITED", "message": "Request rate exceeded"},
                headers={"Retry-After": str(retry)})
        hits.append(now)


def connect():
    connection = mysql.connector.connect(
        host=DB_HOST, port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "weather_user"), password=DB_PASSWORD,
        database=os.getenv("DB_NAME", "weather"), connection_timeout=4)
    cursor = connection.cursor()
    cursor.execute("SET time_zone = '+00:00'")
    cursor.close()
    return connection


def generation(conn):
    """Generation lives in the database, not the container or environment."""
    cur = conn.cursor()
    try:
        cur.execute("CREATE TABLE IF NOT EXISTS weather_metadata ("
                    "meta_key VARCHAR(64) PRIMARY KEY, meta_value VARCHAR(128) NOT NULL)")
        conn.commit()
        value = secrets.token_hex(8)
        cur.execute("INSERT IGNORE INTO weather_metadata (meta_key, meta_value) "
                    "VALUES ('generation', %s)", (value,))
        conn.commit()
        cur.execute("SELECT meta_value FROM weather_metadata WHERE meta_key='generation'")
        return cur.fetchone()[0]
    finally:
        cur.close()


def as_utc(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def observation(row, gen, source="DEMO"):
    ident, created, *measurements = row
    values = {}
    for name, val in zip(FIELDS, measurements):
        if isinstance(val, Decimal):
            val = float(val)
        values[name] = val
    if values["windDirection"] is not None:
        values["windDirection"] %= 360
    return {
        "id": f"{INSTALLATION}-{gen}-{source.lower()}-{ident}",
        "source": source,
        "observedAt": as_utc(created),
        "receivedAt": as_utc(created),
        **values,
        "qualityStatus": "SIMULATED" if source == "DEMO" else "OK",
    }


def source_guard(source):
    if source != "DEMO":
        raise HTTPException(404, {"code": "SOURCE_UNAVAILABLE",
                                  "message": "Hardware collector is not connected"})


def cursor_encode(created, ident, gen, source, end):
    payload = json.dumps([as_utc(created), ident, gen, source, as_utc(end)], separators=(",", ":")).encode()
    signature = hmac.new(TOKEN.encode(), payload, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(payload + signature).decode().rstrip("=")


def cursor_decode(value, gen, source, end):
    try:
        raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        payload, signature = raw[:-32], raw[-32:]
        if not hmac.compare_digest(signature, hmac.new(TOKEN.encode(), payload, hashlib.sha256).digest()):
            raise ValueError("Signature mismatch")
        stamp, ident, saved_gen, saved_source, saved_end = json.loads(payload)
        if saved_gen != gen or saved_source != source or saved_end != as_utc(end):
            raise ValueError("Cursor belongs to another query")
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")).replace(tzinfo=None), int(ident)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise HTTPException(400, {"code": "INVALID_CURSOR", "message": "Invalid or expired cursor"}) from exc


@app.get("/api/v1/health", dependencies=[Depends(authorize)])
def health():
    with connect() as conn:
        gen = generation(conn)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
    return {"status": "ok", "version": "1.2", "installationId": INSTALLATION,
            "databaseGeneration": gen, "database": {"status": "ok", "generation": gen},
            "timestamp": as_utc(datetime.now(timezone.utc))}


@app.get("/api/v1/weather/latest", dependencies=[Depends(authorize)])
def latest(source: str = Query(...)):
    source_guard(source)
    with connect() as conn:
        gen = generation(conn)
        cur = conn.cursor()
        cur.execute("SELECT ID, CREATED, " + ", ".join(COLUMNS) +
                    " FROM dataentry ORDER BY CREATED DESC, ID DESC LIMIT 1")
        row = cur.fetchone()
        cur.close()
    return {"source": source, "observation": observation(row, gen) if row else None}


def parse_time(value, field):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("Missing timezone")
        return parsed.astimezone(timezone.utc)
    except ValueError as exc:
        raise HTTPException(400, {"code": "INVALID_TIMESTAMP",
                                  "message": "Expected ISO 8601 timestamp with timezone",
                                  "field": field}) from exc


@app.get("/api/v1/weather/history", dependencies=[Depends(authorize)])
def history(source: str = Query(...), from_: str = Query(..., alias="from"),
            to: str | None = None, limit: int = Query(500, ge=1, le=2000),
            cursor: str | None = None):
    source_guard(source)
    if cursor and not to:
        raise HTTPException(400, {"code": "INVALID_CURSOR", "message": "Explicit to timestamp required when paging"})
    start = parse_time(from_, "from")
    end = parse_time(to, "to") if to else datetime.now(timezone.utc).replace(microsecond=0)
    if end < start or end - start > timedelta(days=31) or end > datetime.now(timezone.utc) + timedelta(seconds=1):
        raise HTTPException(400, {"code": "INVALID_RANGE", "message": "Invalid date range"})
    with connect() as conn:
        gen = generation(conn)
        cur = conn.cursor()
        params = [start.replace(tzinfo=None), end.replace(tzinfo=None)]
        where = "CREATED >= %s AND CREATED <= %s"
        if cursor:
            stamp, ident = cursor_decode(cursor, gen, source, end)
            where += " AND (CREATED > %s OR (CREATED = %s AND ID > %s))"
            params.extend([stamp, stamp, ident])
        params.append(limit + 1)
        cur.execute("SELECT ID, CREATED, " + ", ".join(COLUMNS) +
                    " FROM dataentry WHERE " + where +
                    " ORDER BY CREATED ASC, ID ASC LIMIT %s", tuple(params))
        rows = cur.fetchall()
        cur.close()
    more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = cursor_encode(rows[-1][1], rows[-1][0], gen, source, end) if more else None
    return {"source": source, "observations": [observation(row, gen) for row in rows],
            "nextCursor": next_cursor}


@app.get("/api/v1/weather/status", dependencies=[Depends(authorize)])
def status():
    with connect() as conn:
        gen = generation(conn)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*), MAX(CREATED) FROM dataentry")
        count, newest = cur.fetchone()
        cur.close()
    return {
        "installationId": INSTALLATION, "databaseGeneration": gen,
        "sources": {
            "DEMO": {"state": "LIVE" if newest and
                     (datetime.now(timezone.utc).replace(tzinfo=None) - newest).total_seconds() <= 60
                     else "STALE" if newest else "NO_DATA",
                     "lastObservationAt": as_utc(newest) if newest else None,
                     "observationCount": count},
            "HARDWARE": {"state": "NO_DATA", "lastObservationAt": None, "observationCount": 0}
        },
        "publishing": {"enabled": False, "providers": [], "lastResult": "none"}
    }
