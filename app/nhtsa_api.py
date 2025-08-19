import httpx
from typing import Dict, List

NHTSA_API_BASE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles"

async def decode_vin_nhtsa(vin: str) -> List[Dict]:
    """Decodes a VIN using the NHTSA API and returns the raw results."""
    url = f"{NHTSA_API_BASE_URL}/decodevin/{vin}?format=json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        return data.get("Results", [])
