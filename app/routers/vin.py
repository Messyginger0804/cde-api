from typing import Optional, List
import base64

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import Response
from sqlalchemy import select

from ..vin_decoder import decode_vin, get_make_from_wmi
from ..db import get_session
from ..models import Vin, VinImage, NHTSADecodedData
from ..auth import verify_auth
from ..nhtsa_api import decode_vin_nhtsa

router = APIRouter(dependencies=[Depends(verify_auth)])

@router.get("/decode/{vin}")
async def decode(vin: str):
    """Return decoded data for a VIN, cached in DB."""
    vin = vin.upper()
    try:
        with get_session() as session:
            obj = session.get(Vin, vin)
            if obj:
                # If VIN exists, return its data and associated NHTSA data
                nhtsa_data_list = [
                    {"variable": d.variable, "value": d.value, "variable_id": d.variable_id, "value_id": d.value_id}
                    for d in obj.nhtsa_data
                ]
                return {
                    "vin": obj.vin,
                    "wmi": obj.wmi,
                    "vds": obj.vds,
                    "vis": obj.vis,
                    "model_year": obj.model_year,
                    "plant": obj.plant,
                    "valid_check_digit": obj.valid_check_digit,
                    "make": obj.make,
                    "model": obj.model,
                    "nhtsa_data": nhtsa_data_list,
                }

            # If VIN not found, decode using NHTSA API
            nhtsa_results = await decode_vin_nhtsa(vin)

            # Extract common fields from NHTSA results
            make = next((item["Value"] for item in nhtsa_results if item["Variable"] == "Make"), None)
            model = next((item["Value"] for item in nhtsa_results if item["Variable"] == "Model"), None)
            model_year = next((int(item["Value"]) for item in nhtsa_results if item["Variable"] == "Model Year" and item["Value"].isdigit()), None)
            plant_city = next((item["Value"] for item in nhtsa_results if item["Variable"] == "Plant City"), None)

            # Create new Vin object
            obj = Vin(
                vin=vin,
                wmi=vin[0:3],
                vds=vin[3:9],
                vis=vin[9:],
                model_year=model_year,
                plant=plant_city, # Using plant_city for plant for now
                valid_check_digit=None, # NHTSA API doesn't directly provide this as a boolean
                make=make,
                model=model,
            )
            session.add(obj)

            # Store all NHTSA decoded data
            for item in nhtsa_results:
                nhtsa_data_entry = NHTSADecodedData(
                    vin=vin,
                    variable=item["Variable"],
                    value=item["Value"],
                    variable_id=item["VariableId"],
                    value_id=item["ValueId"],
                )
                session.add(nhtsa_data_entry)
            session.commit()
            session.refresh(obj)

            # Return the newly created Vin data and NHTSA data
            nhtsa_data_list = [
                {"variable": d.variable, "value": d.value, "variable_id": d.variable_id, "value_id": d.value_id}
                for d in obj.nhtsa_data
            ]
            return {
                "vin": obj.vin,
                "wmi": obj.wmi,
                "vds": obj.vds,
                "vis": obj.vis,
                "model_year": obj.model_year,
                "plant": obj.plant,
                "valid_check_digit": obj.valid_check_digit,
                "make": obj.make,
                "model": obj.model,
                "nhtsa_data": nhtsa_data_list,
            }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=f"NHTSA API error: {exc.response.text}")


@router.get("/decode/{vin}/image")
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


@router.post("/vins/{vin}/image", status_code=201)
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
            # Decode using NHTSA API if VIN not found
            nhtsa_results = await decode_vin_nhtsa(vin)
            make = next((item["Value"] for item in nhtsa_results if item["Variable"] == "Make"), None)
            model = next((item["Value"] for item in nhtsa_results if item["Variable"] == "Model"), None)
            model_year = next((int(item["Value"]) for item in nhtsa_results if item["Variable"] == "Model Year" and item["Value"].isdigit()), None)
            plant_city = next((item["Value"] for item in nhtsa_results if item["Variable"] == "Plant City"), None)

            vin_obj = Vin(
                vin=vin,
                wmi=vin[0:3],
                vds=vin[3:9],
                vis=vin[9:],
                model_year=model_year,
                plant=plant_city,
                valid_check_digit=None,
                make=make,
                model=model,
            )
            session.add(vin_obj)

            for item in nhtsa_results:
                nhtsa_data_entry = NHTSADecodedData(
                    vin=vin,
                    variable=item["Variable"],
                    value=item["Value"],
                    variable_id=item["VariableId"],
                    value_id=item["ValueId"],
                )
                session.add(nhtsa_data_entry)

        session.add(VinImage(vin=vin, content_type=file.content_type or "image/png", data=content))
    return {"status": "ok"}


@router.get("/vins/{vin}/images", response_model=List[dict])
def get_vin_images(vin: str):
    """Return a list of image metadata for a VIN."""
    vin = vin.upper()
    with get_session() as session:
        images = session.execute(
            select(VinImage.id, VinImage.content_type, VinImage.created_at)
            .where(VinImage.vin == vin)
            .order_by(VinImage.created_at.desc())
        ).all()
        if not images:
            raise HTTPException(status_code=404, detail="No images found for this VIN")
        return [
            {"id": img.id, "content_type": img.content_type, "created_at": str(img.created_at)}
            for img in images
        ]


@router.get("/vins/{vin}/images/{image_id}")
def get_vin_image(vin: str, image_id: int):
    """Return a specific image associated with the VIN."""
    vin = vin.upper()
    with get_session() as session:
        img = session.execute(
            select(VinImage)
            .where(VinImage.vin == vin, VinImage.id == image_id)
        ).scalars().first()
        if not img:
            raise HTTPException(status_code=404, detail="Image not found")
        return Response(content=img.data, media_type=img.content_type or "image/png")


@router.get("/images/make/{make}/model/{model}", response_model=List[dict])
def get_images_by_make_model(make: str, model: str):
    """Return a list of image metadata for a given make and model."""
    with get_session() as session:
        images = session.execute(
            select(VinImage.id, VinImage.content_type, VinImage.created_at, Vin.vin)
            .join(Vin)
            .where(Vin.make == make.title(), Vin.model == model.title())
            .order_by(VinImage.created_at.desc())
        ).all()
        if not images:
            raise HTTPException(status_code=404, detail="No images found for this make and model")
        return [
            {"id": img.id, "content_type": img.content_type, "created_at": str(img.created_at), "vin": img.vin}
            for img in images
        ]