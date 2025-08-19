# cde-api

Simple FastAPI service for decoding VINs and serving associated images.

## Setup

```bash
./scripts/start.sh  # creates .venv, installs deps, starts on :8000
```

Auth and DB are configured via environment (auto-creates `.env` on first run):

```bash
export API_TOKEN=devtoken
export DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME
```

## Endpoints

- `GET /decode/{vin}` - Decode a VIN into its component parts.
- `GET /decode/{vin}/image` - Retrieve an image for the VIN (if available).
- `POST /vins/{vin}/image` - Upload and store an image for a VIN.

A sample VIN `1M8GDM9AXKP042788` is included with an in-memory placeholder image.

Open interactive docs at `http://127.0.0.1:8000/docs`.

## Auth

- Send `Authorization: Bearer <API_TOKEN>` with every request.
- Default token for local dev/tests is `devtoken` (set via `.env` or env var `API_TOKEN`).
