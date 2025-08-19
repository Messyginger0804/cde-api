# cde-api

Simple FastAPI service for decoding VINs and serving associated images.

## Setup

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Endpoints

- `GET /decode/{vin}` - Decode a VIN into its component parts.
- `GET /decode/{vin}/image` - Retrieve an image for the VIN (if available).

A sample VIN `1M8GDM9AXKP042788` is included with an in-memory placeholder image.
