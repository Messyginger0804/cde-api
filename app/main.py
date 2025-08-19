import base64
from typing import Optional

from fastapi import FastAPI, Depends
from sqlalchemy import select

from .vin_decoder import decode_vin
from .db import Base, engine, get_session
from .models import Vin, VinImage
from .config import API_TOKEN
from .routers import vin as vin_router


app = FastAPI(title="VIN Decoder API")

app.include_router(vin_router.router)


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