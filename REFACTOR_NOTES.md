# Refactor branch: reliability and data quality

This branch is **not yet production-validated on a Raspberry Pi**. Keep the deployed service on `main` until hardware and service checks pass.

## Changes

- Wind direction now uses a circular mean in the 2-, 5-, and 10-minute SQL aggregation windows. Opposing or missing samples currently fall back to 0 degrees; this should be represented as unavailable in a later schema update.
- The uploader uses the original `dataentry.CREATED` timestamp instead of stamping old observations with the current time.
- Observations older than `max_observation_age_seconds` (default 600) or containing invalid core values are not uploaded.
- HTTP 4xx/5xx responses no longer count as successful submissions. **Some providers return errors in HTTP 200 response bodies; provider-specific acknowledgement parsing is still required.**
- Windy and Weathercloud request credentials are no longer printed in debug logs.
- Log files rotate after 10 MB (five backups).
- The configured database port is honoured.
- Service intervals shorter than 30 seconds are rejected.
- Visual Crossing HTTP calls now have connection/read timeouts, and failed database updates propagate errors instead of silently reporting success.
- Added isolated unit tests for circular wind averaging and observation quality checks.

## Verification

Run `python3 -m unittest discover -s tests -v` from the repository root. The tests do not require hardware or database access.

Before deploying, validate that your MariaDB server supports `ATAN2`, `RADIANS`, `DEGREES`, `SIN`, `COS` and `MOD`; verify timezone configuration and all five provider responses. Confirm rainfall rows represent increments rather than cumulative totals before relying on SUM-based rainfall calculations.

## Outstanding work

1. Provider-specific response acknowledgement validation and 429/backoff handling.
2. One consistent database snapshot instead of repeated queries from each upload thread.
3. Replace shared global cursor/connection with bounded connections and context-managed cursors.
4. Graceful shutdown with a stop event and explicit thread joins.
5. Wire YAML logging options into the logger rather than hardcoded defaults.
6. Store missing measurements as NULL and reject absent wind aggregates instead of treating them as north/calm.
7. Test actual GPIO collection and live dashboard, which are not included in this repository.
8. Add database migration strategy, deployment service unit, and end-to-end tests.
9. Validate provider units, especially Windy precipitation and time conventions, against current API documentation.
