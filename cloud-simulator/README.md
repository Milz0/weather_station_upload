# Cloud-hosted virtual weather station

Runs on any cloud Linux VM with Docker Engine and Docker Compose v2. **No GPIO hardware or Raspberry Pi required.** The virtual sensor inserts realistic changing measurements into the repository's original `dataentry` MariaDB schema. The **actual repository uploader** then reads those measurements and sends HTTP requests to five local mock endpoints.

## Start

From the repository root:

```bash
cd cloud-simulator
docker compose up -d --build
docker compose logs -f sensor uploader mock-services
```

Wait 60–90 seconds to see uploader requests (service interval is 60 seconds). Inspect the latest observations:

```bash
docker compose exec database mariadb -uweather_user -pvirtual-weather-only weather -e "SELECT ID, CREATED, AIR_TEMP, HUMIDITY, WIND_SPEED, WIND_DIRECTION, RAINFALL FROM dataentry ORDER BY ID DESC LIMIT 10;"
```

Stop and preserve observations: `docker compose down`. Stop and **delete** the simulation database: `docker compose down -v`.

## Safety

- The Docker network is marked `internal: true` and no service ports are published to the host. No fabricated weather data can reach the real provider URLs from these containers.
- All five provider URLs are local `mock-services:8080` endpoints. Never replace them with production credentials in this environment.
- The cloud VM needs outbound network access to download Docker images during initial build, but the running containers do not have internet access.
- Database credentials are for the isolated simulation only. If you change `DB_PASSWORD` in Compose, also update the uploader's local YAML configuration.
- For troubleshooting, `docker compose logs --tail=100 uploader` shows errors without needing to expose MariaDB publicly.

## Fault injection

Set `MOCK_FAILURE_RATE=0.5` in an optional `.env` file, then recreate the mock container to return HTTP 503 for approximately half of upload requests. `SENSOR_INTERVAL_SECONDS=15` controls observation frequency, and `SENSOR_SEED=42` controls reproducible random variation. Stop the sensor with `docker compose stop sensor` to verify that stale data is rejected after 10 minutes.

## Limitations

The sensor is a **database-level hardware emulator**, not a full GPIO-pin emulator: the GPIO capture scripts and dashboard source were not present in this repository. Mock endpoints currently validate HTTP request delivery/status, not provider-specific success response bodies. The simulator does not expose a public dashboard. This stack has not yet been exercised against a live cloud Docker runtime.
