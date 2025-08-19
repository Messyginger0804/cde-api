import base64
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select

from .vin_decoder import decode_vin
from .db import Base, engine, get_session
from .models import Vin, VinImage
from .config import API_TOKEN


scheme = HTTPBearer(auto_error=False)


def verify_auth(credentials: HTTPAuthorizationCredentials = Depends(scheme)):
    if not credentials or credentials.scheme.lower() != "bearer" or credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


app = FastAPI(title="VIN Decoder API", dependencies=[Depends(verify_auth)])


# Mapping of sample VINs to base64-encoded image bytes (used to seed DB)
SAMPLE_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII="
)
SAMPLE_VIN = "1M8GDM9AXKP042788"


@app.on_event("startup")
def startup() -> None:
    # Create tables
    Base.metadata.create_all(bind=engine)
    # Seed sample VIN and image if not present
    with get_session() as session:
        vin_obj: Optional[Vin] = session.get(Vin, SAMPLE_VIN)
        if not vin_obj:
            data = decode_vin(SAMPLE_VIN)
            vin_obj = Vin(
                vin=data["vin"],
                wmi=data["wmi"],
                vds=data["vds"],
                vis=data["vis"],
                model_year=data.get("model_year"),
                plant=data.get("plant"),
                valid_check_digit=data.get("valid_check_digit"),
            )
            session.add(vin_obj)
        # add image if none exists
        existing = session.execute(select(VinImage).where(VinImage.vin == SAMPLE_VIN)).scalars().first()
        if not existing:
            session.add(
                VinImage(
                    vin=SAMPLE_VIN,
                    content_type="image/png",
                    data=base64.b64decode(SAMPLE_PNG_BASE64),
                )
            )


@app.get("/decode/{vin}")
def decode(vin: str):
    """Return decoded data for a VIN, cached in DB."""
    vin = vin.upper()
    try:
        with get_session() as session:
            obj = session.get(Vin, vin)
            if obj:
                return {
                    "vin": obj.vin,
                    "wmi": obj.wmi,
                    "vds": obj.vds,
                    "vis": obj.vis,
                    "model_year": obj.model_year,
                    "plant": obj.plant,
                    "valid_check_digit": obj.valid_check_digit,
                }
            data = decode_vin(vin)
            obj = Vin(
                vin=data["vin"],
                wmi=data["wmi"],
                vds=data["vds"],
                vis=data["vis"],
                model_year=data.get("model_year"),
                plant=data.get("plant"),
                valid_check_digit=data.get("valid_check_digit"),
            )
            session.add(obj)
            return data
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/decode/{vin}/image")
def image(vin: str):
    """Return the latest image associated with the VIN."""
    vin = vin.upper()
    with get_session() as session:
        img = (
            session.execute(
                select(VinImage).where(VinImage.vin == vin).order_by(VinImage.created_at.desc())
            )
            .scalars()
            .first()
        )
        if not img:
            raise HTTPException(status_code=404, detail="Image not found")
        return Response(content=img.data, media_type=img.content_type or "image/png")


@app.post("/vins/{vin}/image", status_code=201)
async def upload_image(vin: str, file: UploadFile = File(...)):
    """Upload an image for a VIN and store in DB."""
    vin = vin.upper()
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    with get_session() as session:
        # ensure VIN exists in table (decode and insert if needed)
        vin_obj = session.get(Vin, vin)
        if not vin_obj:
            data = decode_vin(vin)
            vin_obj = Vin(
                vin=data["vin"],
                wmi=data["wmi"],
                vds=data["vds"],
                vis=data["vis"],
                model_year=data.get("model_year"),
                plant=data.get("plant"),
                valid_check_digit=data.get("valid_check_digit"),
            )
            session.add(vin_obj)
        session.add(VinImage(vin=vin, content_type=file.content_type or "image/png", data=content))
    return {"status": "ok"}
