from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
AUTH = {"Authorization": "Bearer devtoken"}


def test_decode_success():
    vin = "1M8GDM9AXKP042788"
    response = client.get(f"/decode/{vin}", headers=AUTH)
    assert response.status_code == 200
    data = response.json()
    assert data["vin"] == vin
    assert data["wmi"] == vin[:3]
    assert data["vds"] == vin[3:9]
    assert data["vis"] == vin[9:]


def test_decode_invalid_length():
    response = client.get("/decode/123", headers=AUTH)
    assert response.status_code == 400


def test_image_endpoint():
    vin = "1M8GDM9AXKP042788"
    response = client.get(f"/decode/{vin}/image", headers=AUTH)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_image_not_found():
    response = client.get("/decode/INVALIDVIN000000/image", headers=AUTH)
    assert response.status_code == 404
