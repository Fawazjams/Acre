# Acre — Cloud (reporting only)

FastAPI service that ingests synced rows from the edge devices and produces the
map, the pesticide summary, and the Claude AI report. **No inference runs here**
— the device already computed the health score; the cloud only aggregates.

Runs on local SQLite by default (zero setup) or Postgres/Supabase in prod.

## Run locally

```bash
pip install -r requirements.txt

# 1. Seed farm + zones + UC IPM treatments + synthetic history
python -m cloud.seed

# 2. Start the API
uvicorn cloud.app.main:app --reload --port 8000
```

Point the edge device at it with `ACRE_BACKEND_URL=http://<host>:8000/api/sync`.

## Use Postgres / Supabase instead of SQLite

```bash
export ACRE_DATABASE_URL="postgresql+psycopg://user:pass@host:5432/postgres"
psql "$ACRE_DATABASE_URL" -f schema.sql     # or let init_db() create tables
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/sync` | Idempotent ingest from devices (PRD 8.6) |
| GET | `/api/farms/{farm_id}/map` | Zones + latest health color for the map |
| GET | `/api/farms/{farm_id}/treatments` | Pesticide summary grouped by zone |
| POST | `/api/farms/{farm_id}/report?period=daily` | Recompute scores + Claude summary |
| GET | `/api/farms/{farm_id}/report/latest` | Most recent stored report |
| GET | `/health` | Liveness |

## AI summary

Set `ANTHROPIC_API_KEY` to use Claude (`claude-sonnet-4-6`). Without a key, a
deterministic offline summary is returned so the demo never hard-fails.

## Docker and CI

```bash
docker build -f cloud/Dockerfile -t acre-cloud .          # run from the repo root
docker run -p 8000:8000 -e ACRE_DATABASE_URL=sqlite:///./acre_cloud.db acre-cloud
```

GitHub Actions (`.github/workflows/ci.yml`) lints, runs `cloud/tests` (sync
idempotency, validation, health, map) and builds the image on every push and PR.

```bash
pip install -r cloud/requirements-dev.txt && pytest cloud/tests -q
```
