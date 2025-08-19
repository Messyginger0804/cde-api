import base64

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

from .vin_decoder import decode_vin

app = FastAPI(title="VIN Decoder API")

# Mapping of sample VINs to base64-encoded image bytes
SAMPLE_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII="
)
IMAGES = {
    "1M8GDM9AXKP042788": base64.b64decode(SAMPLE_PNG_BASE64),
}


@app.get("/decode/{vin}")
def decode(vin: str):
    """Return decoded data for a VIN."""
    try:
        return decode_vin(vin.upper())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/decode/{vin}/image")
def image(vin: str):
    """Return an image associated with the VIN."""
    data = IMAGES.get(vin.upper())
    if not data:
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(content=data, media_type="image/png")
